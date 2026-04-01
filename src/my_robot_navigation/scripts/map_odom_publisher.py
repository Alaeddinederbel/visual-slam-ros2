#!/usr/bin/env python3
"""
Node pour publier la transformation map->odom basée sur la localisation EKF
Remplace AMCL pour fournir la localisation globale à Nav2
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros
from tf2_ros import TransformBroadcaster
import numpy as np

class MapOdomPublisher(Node):
    def __init__(self):
        super().__init__('map_odom_publisher')
        
        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Subscriber pour l'odométrie filtrée (EKF)
        self.filtered_odom_sub = self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self.filtered_odom_callback,
            10
        )
        
        # Subscriber pour l'odométrie brute (encodeurs)
        self.raw_odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.raw_odom_callback,
            10
        )
        
        # Variables pour stocker les poses
        self.filtered_pose = None
        self.raw_pose = None
        self.last_transform_time = None
        
        # Paramètres
        self.publish_rate = 10.0  # Hz
        self.transform_timeout = 0.5  # secondes
        
        # Timer pour publier la transformation
        self.timer = self.create_timer(
            1.0 / self.publish_rate,
            self.publish_transform
        )
        
        self.get_logger().info("Map->Odom publisher initialisé")
    
    def filtered_odom_callback(self, msg):
        """Callback pour l'odométrie filtrée (EKF)"""
        self.filtered_pose = msg.pose.pose
        self.last_transform_time = self.get_clock().now()
    
    def raw_odom_callback(self, msg):
        """Callback pour l'odométrie brute"""
        self.raw_pose = msg.pose.pose
    
    def publish_transform(self):
        """Publie la transformation map->odom"""
        if self.filtered_pose is None or self.raw_pose is None:
            return
        
        # Vérifier que les données ne sont pas trop anciennes
        current_time = self.get_clock().now()
        if self.last_transform_time is None:
            return
        
        time_diff = (current_time - self.last_transform_time).nanoseconds / 1e9
        if time_diff > self.transform_timeout:
            self.get_logger().warn("Données de localisation trop anciennes")
            return
        
        try:
            # Calculer la transformation map->odom
            # map_T_base = filtered_pose (position globale du robot)
            # odom_T_base = raw_pose (position dans le frame odom)
            # map_T_odom = map_T_base * inv(odom_T_base)
            
            transform = TransformStamped()
            transform.header.stamp = current_time.to_msg()
            transform.header.frame_id = 'map'
            transform.child_frame_id = 'odom'
            
            # Position du robot dans map (filtrée)
            map_x = self.filtered_pose.position.x
            map_y = self.filtered_pose.position.y
            map_z = self.filtered_pose.position.z
            
            # Position du robot dans odom (brute)
            odom_x = self.raw_pose.position.x
            odom_y = self.raw_pose.position.y
            odom_z = self.raw_pose.position.z
            
            # Transformation map->odom (approximation 2D)
            transform.transform.translation.x = map_x - odom_x
            transform.transform.translation.y = map_y - odom_y
            transform.transform.translation.z = map_z - odom_z
            
            # Orientation (différence entre filtered et raw)
            # Simplification: utiliser directement l'orientation filtrée
            # Pour une implémentation complète, il faudrait calculer la différence
            map_quat = self.filtered_pose.orientation
            odom_quat = self.raw_pose.orientation
            
            # Approximation: utiliser la différence d'orientation
            # (Pour une implémentation robuste, utiliser des quaternions)
            map_yaw = self.quaternion_to_yaw(map_quat)
            odom_yaw = self.quaternion_to_yaw(odom_quat)
            yaw_diff = map_yaw - odom_yaw
            
            # Normaliser l'angle
            while yaw_diff > np.pi:
                yaw_diff -= 2 * np.pi
            while yaw_diff < -np.pi:
                yaw_diff += 2 * np.pi
            
            # Convertir en quaternion
            transform.transform.rotation = self.yaw_to_quaternion(yaw_diff)
            
            # Publier la transformation
            self.tf_broadcaster.sendTransform(transform)
            
        except Exception as e:
            self.get_logger().error(f"Erreur dans le calcul de transformation: {e}")
    
    def quaternion_to_yaw(self, quat):
        """Convertit un quaternion en angle yaw"""
        siny_cosp = 2 * (quat.w * quat.z + quat.x * quat.y)
        cosy_cosp = 1 - 2 * (quat.y * quat.y + quat.z * quat.z)
        return np.arctan2(siny_cosp, cosy_cosp)
    
    def yaw_to_quaternion(self, yaw):
        """Convertit un angle yaw en quaternion"""
        from geometry_msgs.msg import Quaternion
        quat = Quaternion()
        quat.x = 0.0
        quat.y = 0.0
        quat.z = np.sin(yaw / 2.0)
        quat.w = np.cos(yaw / 2.0)
        return quat

def main(args=None):
    rclpy.init(args=args)
    node = MapOdomPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()