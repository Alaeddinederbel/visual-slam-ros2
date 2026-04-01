#!/usr/bin/env python3

import sys
import os
# Ajouter le chemin de votre environnement virtuel
sys.path.insert(0, '/media/msi/128873F28873D329/venvs/yolov8_env/lib/python3.10/site-packages')

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
import json
import datetime
import threading
import time

class YOLODetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector_node')
        
        # Initialisation du bridge CV
        self.bridge = CvBridge()
        
        # Charger le modèle YOLOv8 pré-entraîné
        self.model = YOLO('yolov8n.pt')  # Modèle nano, plus rapide
        
        # Variables pour stocker la pose actuelle
        self.current_pose = None
        self.pose_lock = threading.Lock()
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image,
            '/camera/left/left_camera/image_raw',
            self.image_callback,
            10
        )
        
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/orb_slam3/camera_pose',
            self.pose_callback,
            10
        )
        
        # Publisher pour les détections
        self.detection_pub = self.create_publisher(
            String,
            '/yolo/detections',
            10
        )
        
        # Configuration
        self.confidence_threshold = 0.5
        self.detection_interval = 1.0  # Détecter chaque seconde
        self.last_detection_time = 0
        
        # Créer le dossier logs s'il n'existe pas
        self.log_dir = os.path.join(os.path.expanduser('~'), 'ros2_ws/src/my_robot_navigation/logs')
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, 'detected_objects.log')
        
        # Initialiser le fichier log
        self.init_log_file()
        
        self.get_logger().info('YOLOv8 Detector Node initialized')
    
    def init_log_file(self):
        """Initialise le fichier de log avec les en-têtes"""
        with open(self.log_file, 'w') as f:
            f.write("YOLO Object Detection Log\n")
            f.write("========================\n")
            f.write(f"Session started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("Format: [TIMESTAMP] Object: CLASS_NAME, Confidence: XX.XX%, Position: (x, y, z)\n\n")
    
    def pose_callback(self, msg):
        """Callback pour recevoir la pose du robot depuis ORB-SLAM3"""
        with self.pose_lock:
            self.current_pose = msg
    
    def image_callback(self, msg):
        """Callback pour traiter les images de la caméra"""
        current_time = time.time()
        
        # Limiter la fréquence de détection pour éviter la surcharge
        if current_time - self.last_detection_time < self.detection_interval:
            return
        
        try:
            # Convertir l'image ROS en OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # Effectuer la détection YOLO
            results = self.model(cv_image, conf=self.confidence_threshold)
            
            # Traiter les résultats
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extraire les informations de détection
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = self.model.names[class_id]
                        
                        # Coordonnées de la boîte englobante
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        detection_data = {
                            'class_name': class_name,
                            'confidence': confidence,
                            'bbox': [x1, y1, x2, y2],
                            'timestamp': datetime.datetime.now().isoformat()
                        }
                        
                        detections.append(detection_data)
            
            # Logger les détections
            if detections:
                self.log_detections(detections)
                
                # Publier les détections
                detection_msg = String()
                detection_msg.data = json.dumps(detections)
                self.detection_pub.publish(detection_msg)
            
            self.last_detection_time = current_time
            
        except Exception as e:
            self.get_logger().error(f'Erreur lors du traitement de l\'image: {str(e)}')
    
    def log_detections(self, detections):
        """Enregistre les détections dans le fichier log"""
        with self.pose_lock:
            current_pose = self.current_pose
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        with open(self.log_file, 'a') as f:
            for detection in detections:
                pose_str = "Unknown"
                if current_pose:
                    pose = current_pose.pose.position
                    pose_str = f"({pose.x:.3f}, {pose.y:.3f}, {pose.z:.3f})"
                
                log_entry = (
                    f"[{timestamp}] Object: {detection['class_name']}, "
                    f"Confidence: {detection['confidence']:.2%}, "
                    f"Position: {pose_str}\n"
                )
                f.write(log_entry)
        
        self.get_logger().info(f'Logged {len(detections)} détections')

def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = YOLODetectorNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Erreur: {e}')
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()