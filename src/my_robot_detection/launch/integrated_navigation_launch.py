#!/usr/bin/env python3
# Fichier: ~/ros2_ws/src/my_robot_perception/launch/integrated_navigation_launch.py

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, EnvironmentVariable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition 
import os

def generate_launch_description():
    # Déclaration des arguments
    use_yolo_arg = DeclareLaunchArgument(
        'use_yolo',
        default_value='true',
        description='Active ou désactive la détection avec YOLOv8'
    )
    
    use_orbslam_arg = DeclareLaunchArgument(
        'use_orbslam',
        default_value='true',
        description='Active ou désactive ORB-SLAM3'
    )
    
    use_rtabmap_arg = DeclareLaunchArgument(
        'use_rtabmap',
        default_value='true',
        description='Active ou désactive RTAB-Map'
    )
    
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolov8n.pt',
        description='Chemin vers le modèle YOLOv8'
    )
    
    # Chemins des packages
    orbslam_share = FindPackageShare('orbslam3_ros2')
    rtabmap_config_share = FindPackageShare('my_rtabmap_config')
    robot_bringup_share = FindPackageShare('my_robot_bringup')
    robot_detection_share = FindPackageShare('my_robot_detection')
    
    # PYTHONPATH pour l'environnement virtuel YOLOv8
    venv_pythonpath = SetEnvironmentVariable(
        name='PYTHONPATH',
        value=['/media/msi/128873F28873D329/venvs/yolov8_env/lib/python3.10/site-packages:',
               EnvironmentVariable('PYTHONPATH', default_value='')]
    )
    
    # Lancement du robot (supposé existant dans my_robot_bringup)
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([robot_bringup_share, 'launch', 'my_robot_gazebo.launch.py'])
        ])
    )
    
    # Lancement d'ORB-SLAM3 (si activé)
    orbslam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([orbslam_share, 'launch', 'stereo.launch.py'])
        ]),
        condition=IfCondition(LaunchConfiguration('use_orbslam'))   
    )
    
    # Lancement de RTAB-Map (si activé)
    rtabmap_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([rtabmap_config_share, 'launch', 'rtabmap_stereo.launch.py'])
        ]),
        condition=IfCondition(LaunchConfiguration('use_rtabmap')) 
    )
    
    # Lancement de YOLOv8 (si activé)
    yolov8_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([robot_detection_share, 'launch', 'yolov8_launch.py'])
        ]),
        launch_arguments={
            'model_path': LaunchConfiguration('model_path'),
        }.items(),
        condition=IfCondition(LaunchConfiguration('use_yolo')) 
    )
    
    # Nœud d'intégration pour la navigation
  #  integrated_navigation_node = Node(
   #     package='my_robot_perception',
    #    executable='integrated_navigation_node',
     #   name='integrated_navigation',
      #  output='screen',
      #  parameters=[{
       #     'detection_topic': '/yolov8/detections',
        #    'cmd_vel_topic': '/cmd_vel',
         #   'odom_topic': '/odom',
          #  'object_avoidance_distance': 1.0,
           # 'object_interest_classes': ['person', 'chair', 'bottle', 'laptop', 'tv', 'cell phone'],
           # 'camera_frame': 'camera_link',
           # 'base_frame': 'base_footprint'
        #}]
   # )
    
    # Créer et retourner la description de lancement
    return LaunchDescription([
        venv_pythonpath,
        use_yolo_arg,
        use_orbslam_arg,
        use_rtabmap_arg,
        model_path_arg,
        robot_launch,
        orbslam_launch,
        rtabmap_launch,
        yolov8_launch,
        #integrated_navigation_node
    ])