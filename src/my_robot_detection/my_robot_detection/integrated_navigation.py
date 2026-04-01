#!/usr/bin/env python3
# Fichier: ~/ros2_ws/src/my_robot_perception/my_robot_perception/integrated_navigation.py

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from vision_msgs.msg import Detection2DArray
from std_msgs.msg import String
import math
import numpy as np
from tf2_ros import Buffer, TransformListener
import tf2_ros
import time

class IntegratedNavigationNode(Node):
    def __init__(self):
        super().__init__('integrated_navigation_node')
        
        # Paramètres
        self.declare_parameter('detection_topic', '/yolov8/detections')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('object_avoidance_distance', 1.0)  # Distance minimale pour éviter les objets détectés
        self.declare_parameter('object_interest_classes', ['person', 'chair', 'bottle'])  # Classes d'intérêt
        self.declare_parameter('camera_frame', 'camera_link')
        self.declare_parameter('base_frame', 'base_footprint')
        
        detection_topic = self.get_parameter('detection_topic').get_parameter_value().string_value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').get_parameter_value().string_value
        odom_topic = self.get_parameter('odom_topic').get_parameter_value().string_value
        self.object_avoidance_distance = self.get_parameter('object_avoidance_distance').get_parameter_value().double_value
        self.object_interest_classes = self.get_parameter('object_interest_classes').get_parameter_value().string_array_value
        self.camera_frame = self.get_parameter('camera_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value
        
        # Configuration QoS pour la communication temps réel
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        # Abonnements
        self.detection_sub = self.create_subscription(
            Detection2DArray,
            detection_topic,
            self.detection_callback,
            10
        )
        
        self.odom_sub = self.create_subscription(
            Odometry,
            odom_topic,
            self.odom_callback,
            qos_profile
        )
        
        # Éditeurs
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            cmd_vel_topic,
            10
        )
        
        self.status_pub = self.create_publisher(
            String,
            '/navigation/status',
            10
        )
        
        # Configuration de TF2
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Variables d'état
        self.current_pose = None
        self.current_detected_objects = []
        self.last_detection_time = self.get_clock().now()
        self.detection_timeout = 1.0  # 1 seconde sans détection = pas d'objet
        self.exploring = False
        self.approach_target = None
        
        # Timers pour les comportements
        self.timer = self.create_timer(0.1, self.navigation_control_loop)
        
        self.get_logger().info('Nœud de navigation intégrée avec YOLOv8 initialisé')
    
    def detection_callback(self, msg):
        """Callback pour les détections d'objets avec YOLOv8"""
        current_time = self.get_clock().now()
        
        # Filtrer les détections par classe d'intérêt
        self.current_detected_objects = []
        
        for detection in msg.detections:
            if len(detection.results) > 0:
                class_id = int(detection.results[0].id)
                class_name = self.get_class_name(class_id)
                confidence = detection.results[0].score
                
                # Vérifier si la classe est dans celles d'intérêt
                if class_name in self.object_interest_classes and confidence > 0.5:
                    self.current_detected_objects.append({
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': {
                            'center_x': detection.bbox.center.x,
                            'center_y': detection.bbox.center.y,
                            'size_x': detection.bbox.size_x,
                            'size_y': detection.bbox.size_y
                        },
                        'frame_id': msg.header.frame_id
                    })
        
        self.last_detection_time = current_time
        
        # Publier un message d'état si des objets sont détectés
        if self.current_detected_objects:
            objects_str = ", ".join([f"{obj['class_name']} ({obj['confidence']:.2f})" for obj in self.current_detected_objects])
            self.publish_status(f"Objets détectés: {objects_str}")
    
    def odom_callback(self, msg):
        """Callback pour la mise à jour de l'odométrie"""
        self.current_pose = msg.pose.pose
    
    def navigation_control_loop(self):
        """Boucle principale de contrôle de navigation intégrant SLAM et détection d'objets"""
        # Vérifier si nous avons des données valides
        if self.current_pose is None:
            return
        
        cmd_vel = Twist()
        
        # Vérifier si les détections sont récentes
        current_time = self.get_clock().now()
        if (current_time - self.last_detection_time).nanoseconds / 1e9 > self.detection_timeout:
            self.current_detected_objects = []
        
        # Si nous avons des objets détectés, réagir en conséquence
        if self.current_detected_objects:
            # Choisir l'objet le plus intéressant (pour l'instant, le premier)
            target_object = self.current_detected_objects[0]
            
            # Calculer la position approximative 3D de l'objet
            # Note: Ceci est une approximation simple, une meilleure approche utiliserait 
            # des informations de profondeur des caméras stéréo et TF2
            target_frame = target_object['frame_id']
            object_distance = self.estimate_object_distance(target_object)
            
            # Logique de navigation basée sur les objets détectés
            if target_object['class_name'] == 'person':
                # S'arrêter et observer la personne
                cmd_vel.linear.x = 0.0
                cmd_vel.angular.z = 0.0
                self.publish_status(f"Personne détectée à {object_distance:.2f}m - Arrêt")
                
            elif object_distance < self.object_avoidance_distance:
                # Éviter l'objet
                cmd_vel.linear.x = -0.1  # Reculer lentement
                cmd_vel.angular.z = 0.5  # Tourner pour éviter
                self.publish_status(f"Évitement d'objet {target_object['class_name']} à {object_distance:.2f}m")
                
            else:
                # S'approcher de l'objet intéressant mais garder une distance de sécurité
                approach_speed = min(0.2, (object_distance - self.object_avoidance_distance) * 0.5)
                cmd_vel.linear.x = max(0.0, approach_speed)
                
                # Centrer l'objet dans le champ de vision
                image_center_x = 320  # Supposons une largeur d'image de 640px
                object_center_x = target_object['bbox']['center_x']
                angular_error = (object_center_x - image_center_x) / image_center_x
                cmd_vel.angular.z = -angular_error * 0.5
                
                self.publish_status(f"Approche de {target_object['class_name']} à {object_distance:.2f}m")
        else:
            # Mode exploration quand aucun objet n'est détecté
            if not self.exploring:
                self.exploring = True
                self.publish_status("Mode exploration activé")
            
            # Simple comportement d'exploration
            cmd_vel.linear.x = 0.2
            cmd_vel.angular.z = 0.1 * math.sin(time.time())
        
        # Publier la commande de vitesse
        self.cmd_vel_pub.publish(cmd_vel)
    
    def estimate_object_distance(self, object_data):
        """Estimer grossièrement la distance à un objet détecté (sans information de profondeur)"""
        # Dans un système réel, vous utiliseriez des caméras stéréo ou un capteur de profondeur
        # Pour cette démonstration, nous utilisons simplement la taille apparente du rectangle
        # Plus le rectangle est grand, plus l'objet est proche
        box_area = object_data['bbox']['size_x'] * object_data['bbox']['size_y']
        image_area = 640 * 480  # Supposons une résolution de 640x480
        
        # Formule approximative: plus le ratio est grand, plus l'objet est proche
        area_ratio = box_area / image_area
        
        # Conversion arbitraire en distance (à calibrer dans un système réel)
        estimated_distance = 5.0 * (1.0 - math.sqrt(area_ratio))
        return max(0.1, estimated_distance)
    
    def get_class_name(self, class_id):
        """Obtenir le nom de la classe à partir de l'ID de classe YOLOv8 COCO"""
        # Classes COCO simplifiées (pas la liste complète)
        coco_classes = {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 
            5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 
            10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench', 
            14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 
            20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack', 
            25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee', 
            30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat', 
            35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 
            39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 
            44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 
            49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 
            54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 
            59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop'
        }
        
        return coco_classes.get(class_id, f"unknown_{class_id}")
    
    def publish_status(self, status_msg):
        """Publier un message d'état"""
        msg = String()
        msg.data = status_msg
        self.status_pub.publish(msg)
        self.get_logger().info(status_msg)

def main(args=None):
    rclpy.init(args=args)
    node = IntegratedNavigationNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()