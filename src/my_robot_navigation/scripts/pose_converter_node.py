#!/usr/bin/env python3
"""
Node pour convertir la pose d'ORB-SLAM3 vers un format compatible EKF
Gère les transformations de frame et la qualité de la pose
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
import tf2_ros
import tf2_geometry_msgs
from tf2_ros import Buffer, TransformListener
import numpy as np

class PoseConverterNode(Node):
    def __init__(self):
        super().__init__('pose_converter')
        
        # TF2 buffer pour les transformations
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Subscriber pour ORB-SLAM3 pose
        self.orb_pose_sub = self.create_subscription(
            PoseStamped,
            '/orb_slam3/camera_pose',
            self.orb_pose_callback,
            10
        )
        
        # Publisher pour pose avec covariance (pour EKF)
        self.pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/orb_slam3/pose_with_cov',
            10
        )
        
        # Statistiques pour évaluer la qualité
        self.pose_history = []
        self.max_history = 10
        self.last_pose_time = None
        
        # Paramètres de qualité
        self.min_translation_threshold = 0.001  # m
        self.max_translation_jump = 0.5  # m
        self.pose_timeout = 1.0  # secondes
        
        self.get_logger().info("Convertisseur de pose ORB-SLAM3 initialisé")
    
    def orb_pose_callback(self, msg):
        try:
            # Transformer de camera_link vers base_link
            transformed_pose = self.transform_pose(msg, 'base_footprint')
            if transformed_pose is None:
                return
            
            # Évaluer la qualité de la pose
            quality_score = self.evaluate_pose_quality(transformed_pose)
            
            # Créer le message avec covariance adaptative
            pose_with_cov = PoseWithCovarianceStamped()
            pose_with_cov.header = transformed_pose.header
            pose_with_cov.header.frame_id = 'map'  # ORB-SLAM3 travaille en frame map
            pose_with_cov.pose.pose = transformed_pose.pose
            
            # Covariance adaptative basée sur la qualité
            covariance = self.compute_adaptive_covariance(quality_score)
            pose_with_cov.pose.covariance = covariance
            
            # Publier
            self.pose_pub.publish(pose_with_cov)
            
            # Mettre à jour l'historique
            self.update_pose_history(transformed_pose)
            
        except Exception as e:
            self.get_logger().warn(f"Erreur dans conversion pose: {e}")
    
    def transform_pose(self, pose_stamped, target_frame):
        """Transforme la pose vers le frame cible"""
        try:
            # Attendre la transformation
            transform = self.tf_buffer.lookup_transform(
                target_frame,
                pose_stamped.header.frame_id,
                pose_stamped.header.stamp,
                timeout=rclpy.duration.Duration(seconds=0.1)
            )
            
            # Appliquer la transformation
            transformed_pose = tf2_geometry_msgs.do_transform_pose(
                pose_stamped, transform
            )
            
            return transformed_pose
            
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, 
                tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f"Impossible de transformer la pose: {e}")
            return None
    
    def evaluate_pose_quality(self, pose_stamped):
        """Évalue la qualité de la pose (0=mauvaise, 1=excellente)"""
        quality_factors = []
        
        # 1. Continuité temporelle
        current_time = self.get_clock().now()
        if self.last_pose_time is not None:
            time_diff = (current_time - self.last_pose_time).nanoseconds / 1e9
            if time_diff > self.pose_timeout:
                quality_factors.append(0.3)  # Pénalité pour interruption
            else:
                quality_factors.append(1.0)
        
        # 2. Stabilité spatiale
        if len(self.pose_history) > 1:
            last_pose = self.pose_history[-1]
            current_pos = pose_stamped.pose.position
            last_pos = last_pose.pose.position
            
            translation_diff = np.sqrt(
                (current_pos.x - last_pos.x)**2 +
                (current_pos.y - last_pos.y)**2 +
                (current_pos.z - last_pos.z)**2
            )
            
            if translation_diff > self.max_translation_jump:
                quality_factors.append(0.2)  # Saut trop important
            elif translation_diff < self.min_translation_threshold:
                quality_factors.append(0.8)  # Très stable
            else:
                quality_factors.append(1.0)  # Normal
        
        # 3. Consistance de l'orientation
        if len(self.pose_history) > 2:
            # Calculer la variance de l'orientation récente
            recent_yaws = []
            for pose in self.pose_history[-3:]:
                quat = pose.pose.orientation
                yaw = np.arctan2(
                    2.0 * (quat.w * quat.z + quat.x * quat.y),
                    1.0 - 2.0 * (quat.y * quat.y + quat.z * quat.z)
                )
                recent_yaws.append(yaw)
            
            yaw_variance = np.var(recent_yaws)
            if yaw_variance < 0.01:  # Très stable
                quality_factors.append(1.0)
            elif yaw_variance < 0.1:  # Acceptable
                quality_factors.append(0.8)
            else:  # Instable
                quality_factors.append(0.4)
        
        # Score final (moyenne pondérée)
        if quality_factors:
            return np.mean(quality_factors)
        else:
            return 0.7  # Score par défaut
    
    def compute_adaptive_covariance(self, quality_score):
        """Calcule la covariance en fonction de la qualité"""
        # Covariance de base (bonne qualité)
        base_cov = [
            1e-6, 0, 0, 0, 0, 0,     # x
            0, 1e-6, 0, 0, 0, 0,     # y  
            0, 0, 1e-6, 0, 0, 0,     # z
            0, 0, 0, 1e6, 0, 0,      # roll (ignoré)
            0, 0, 0, 0, 1e6, 0,      # pitch (ignoré)
            0, 0, 0, 0, 0, 1e-4      # yaw
        ]
        
        # Ajuster selon la qualité (plus la qualité est faible, plus la covariance augmente)
        quality_factor = max(0.1, quality_score)  # Éviter division par zéro
        scaling_factor = 1.0 / quality_factor
        
        # Appliquer le facteur d'échelle aux éléments de position et orientation
        adapted_cov = base_cov.copy()
        adapted_cov[0] *= scaling_factor    # x
        adapted_cov[7] *= scaling_factor    # y
        adapted_cov[14] *= scaling_factor   # z
        adapted_cov[35] *= scaling_factor   # yaw
        
        return adapted_cov
    
    def update_pose_history(self, pose_stamped):
        """Met à jour l'historique des poses"""
        self.pose_history.append(pose_stamped)
        if len(self.pose_history) > self.max_history:
            self.pose_history.pop(0)
        
        self.last_pose_time = self.get_clock().now()

def main(args=None):
    rclpy.init(args=args)
    node = PoseConverterNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()