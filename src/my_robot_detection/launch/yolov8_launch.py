#!/usr/bin/env python3
# Fichier: ~/ros2_ws/src/my_robot_detection/launch/yolov8_launch.py

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    # Déclaration des arguments
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolov8n.pt',
        description='Chemin vers le modèle YOLOv8 à utiliser'
    )
    
    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='Seuil de confiance pour les détections YOLOv8'
    )
    
    input_topic_left_arg = DeclareLaunchArgument(
        'input_topic_left',
        default_value='/camera/left/left_camera/image_raw',
        description='Topic d\'entrée pour l\'image de la caméra gauche'
    )

    output_topic_arg = DeclareLaunchArgument(
        'output_topic',
        default_value='/yolov8/detections',
        description='Topic de sortie pour les détections YOLOv8'
    )
    
    visualization_topic_arg = DeclareLaunchArgument(
        'visualization_topic',
        default_value='/yolov8/visualization',
        description='Topic de sortie pour la visualisation des détections'
    )
    
    # Définition du nœud YOLOv8
    yolov8_node = Node(
        package='my_robot_detection',
        executable='yolov8_node',
        name='yolov8_node',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'confidence_threshold': LaunchConfiguration('confidence_threshold'),
            'input_topic_left': LaunchConfiguration('input_topic_left'),
            'output_topic': LaunchConfiguration('output_topic'),
            'visualization_topic': LaunchConfiguration('visualization_topic'),
        }]
    )
    
    return LaunchDescription([
        model_path_arg,
        confidence_threshold_arg,
        input_topic_left_arg,
        output_topic_arg,
        visualization_topic_arg,
        yolov8_node
    ])