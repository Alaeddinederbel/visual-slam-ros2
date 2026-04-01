#!/usr/bin/env python3
import os
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
   
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    # YOLOv8 Object Detection Node - CORRIGÉ
    yolo_detector = Node(
        package='my_robot_detection',
        executable='yolov8_detector',
        name='yolov8_detector',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'model': 'yolov8n.pt',
            'confidence_threshold': 0.5,
            'device': 'cpu'
        }],
        remappings=[
            # IMPORTANT: Remapper l'entrée image vers votre caméra
            ('image_raw', '/camera/left/left_camera/image_raw'),  # Changez selon votre topic caméra
            ('image_info', '/camera/left/left_camera/image_info'),
        ]
    )
    
    # Image view for YOLO - avec output screen pour debug
    yolo_image_view = Node(
        package='image_view',
        executable='image_view',
        name='yolo_image_view',
        output='screen',
        remappings=[
            ('image', '/yolo/image_annotated')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )
    
    # Node pour visualiser l'image d'entrée (debug)
    input_image_view = Node(
        package='image_view',
        executable='image_view',
        name='input_image_view',
        output='screen',
        remappings=[
            ('image', '/camera/left/left_camera/image_raw')  # Même topic que l'entrée YOLO
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )
    

    return LaunchDescription([
        declare_use_sim_time_cmd,
        yolo_detector,
        yolo_image_view,
        # input_image_view,  # Décommentez pour debug
    ])