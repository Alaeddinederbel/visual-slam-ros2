#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    
    # Déclaration des arguments de lancement
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    # Chemin vers les fichiers de configuration
    config_file = PathJoinSubstitution([
        FindPackageShare('my_robot_navigation'),
        'config',
        'yolo_config.yaml'
    ])
    
    # Nœud de détection YOLO
    yolo_detector_node = Node(
        package='my_robot_navigation',
        executable='yolo_detector_node.py',
        name='yolo_detector',
        output='screen',
        parameters=[
            config_file,
            {'use_sim_time': use_sim_time}
        ],
        remappings=[
            ('/image_raw', '/camera/left/left_camera/image_raw'),
            ('/camera_pose', '/orb_slam3/camera_pose')
        ]
    )
    
    # Nœud pour l'analyse des logs (optionnel)
    log_analyzer_node = Node(
        package='my_robot_navigation',
        executable='object_logger.py',
        name='object_logger',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time if true'
        ),
        
        yolo_detector_node,
        log_analyzer_node,
    ])