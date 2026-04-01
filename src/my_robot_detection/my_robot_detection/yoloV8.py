#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
import time

class YOLOv8Detector(Node):
    def __init__(self):
        super().__init__('yolov8_detector')
        
        # Paramètres
        self.model_path = self.declare_parameter('model', 'yolov8n.pt').value
        self.confidence_threshold = self.declare_parameter('confidence_threshold', 0.5).value
        self.device = self.declare_parameter('device', 'cpu').value
        
        # Compteurs pour debug
        self.images_received = 0
        self.images_processed = 0
        self.last_log_time = time.time()
        
        try:
            # Initialiser YOLO
            self.get_logger().info(f'Loading YOLO model: {self.model_path}')
            self.model = YOLO(self.model_path)
            self.get_logger().info(f'YOLO model loaded successfully on device: {self.device}')
        except Exception as e:
            self.get_logger().error(f'Failed to load YOLO model: {str(e)}')
            return
        
        self.bridge = CvBridge()
        
        # Subscriber et Publisher
        self.subscription = self.create_subscription(
            Image,
            'image_raw',  # Topic d'entrée (sera remappé)
            self.image_callback,
            10
        )
        
        self.info_subscription = self.create_subscription(
            CameraInfo,
            'image_info',  # Topic d'info caméra (sera remappé)
            self.camera_info_callback,
            10
        )
        
        self.publisher = self.create_publisher(
            Image,
            '/yolo/image_annotated',  # Topic de sortie
            10
        )
        
        self.camera_info_publisher = self.create_publisher(
            CameraInfo,
            '/yolo/camera_info',  # Info caméra de sortie
            10
        )
        
        # Timer pour les statistiques
        self.timer = self.create_timer(5.0, self.log_statistics)
        
        self.get_logger().info('YOLOv8 Detector initialized and waiting for images...')
        self.get_logger().info(f'Subscribed to: {self.subscription.topic_name}')
        self.get_logger().info(f'Publishing to: /yolo/image_annotated')
    
    def camera_info_callback(self, msg):
        # Republier les infos caméra
        self.camera_info_publisher.publish(msg)
    
    def image_callback(self, msg):
        self.images_received += 1
        
        try:
            start_time = time.time()
            
            # Log première image reçue
            if self.images_received == 1:
                self.get_logger().info('First image received! Processing...')
                self.get_logger().info(f'Image size: {msg.width}x{msg.height}, encoding: {msg.encoding}')
            
            # Convertir ROS Image vers OpenCV
            if msg.encoding == 'rgb8':
                cv_image = self.bridge.imgmsg_to_cv2(msg, 'rgb8')
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            else:
                cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # Vérifier que l'image n'est pas vide
            if cv_image is None or cv_image.size == 0:
                self.get_logger().warn('Received empty image')
                return
            
            # Détection YOLO
            results = self.model(cv_image, conf=self.confidence_threshold, device=self.device)
            
            # Annoter l'image
            annotated_image = results[0].plot()
            
            # Log des détections
            detections = results[0].boxes
            if detections is not None and len(detections) > 0:
                num_detections = len(detections)
                if self.images_processed % 30 == 0:  # Log toutes les 30 images
                    self.get_logger().info(f'Detected {num_detections} objects')
            
            # Convertir vers ROS Image et publier
            if msg.encoding == 'rgb8':
                annotated_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
                ros_image = self.bridge.cv2_to_imgmsg(annotated_rgb, 'rgb8')
            else:
                ros_image = self.bridge.cv2_to_imgmsg(annotated_image, 'bgr8')
            
            ros_image.header = msg.header  # Garder le même header
            ros_image.header.frame_id = msg.header.frame_id
            
            self.publisher.publish(ros_image)
            self.images_processed += 1
            
            # Log performance
            processing_time = time.time() - start_time
            if self.images_processed == 1:
                self.get_logger().info(f'First image processed in {processing_time:.3f}s and published!')
            
        except Exception as e:
            self.get_logger().error(f'Error in image processing: {str(e)}')
            import traceback
            self.get_logger().error(f'Traceback: {traceback.format_exc()}')
    
    def log_statistics(self):
        current_time = time.time()
        time_diff = current_time - self.last_log_time
        
        if time_diff > 0:
            input_rate = self.images_received / time_diff if time_diff > 0 else 0
            output_rate = self.images_processed / time_diff if time_diff > 0 else 0
            
            self.get_logger().info(
                f'Stats: Received {self.images_received} images ({input_rate:.1f} Hz), '
                f'Processed {self.images_processed} images ({output_rate:.1f} Hz)'
            )
        
        # Reset counters
        self.images_received = 0
        self.images_processed = 0
        self.last_log_time = current_time

def main(args=None):
    rclpy.init(args=args)
    
    try:
        detector = YOLOv8Detector()
        rclpy.spin(detector)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if 'detector' in locals():
            detector.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()