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
   map_yaml_file = LaunchConfiguration('map')
   params_file = LaunchConfiguration('params_file')


   declare_use_sim_time_cmd = DeclareLaunchArgument(
       'use_sim_time',
       default_value='true',
       description='Use simulation (Gazebo) clock if true'
   )


   declare_map_yaml_cmd = DeclareLaunchArgument(
       'map',
       default_value=PathJoinSubstitution([
           FindPackageShare('my_robot_navigation'),
           'maps',
           'my_carte.yaml'
       ]),
       description='Full path to map yaml file to load'
   )


   declare_params_file_cmd = DeclareLaunchArgument(
       'params_file',
       default_value=PathJoinSubstitution([
           FindPackageShare('my_robot_navigation'),
           'config',
           'nav2_params.yaml'
       ]),
       description='Full path to the ROS2 parameters file to use'
   )


   # Navigation launch avec map_server intégré
   nav2_bringup = IncludeLaunchDescription(
       PythonLaunchDescriptionSource(
           PathJoinSubstitution([
               FindPackageShare('nav2_bringup'),
               'launch',
               'bringup_launch.py'
           ])
       ),
       launch_arguments={
           'use_sim_time': use_sim_time,
           'params_file': params_file,
           'map': map_yaml_file,
           'slam': 'False',
           'use_respawn': 'False',
           'use_namespace': 'False',
           'namespace': '',
           'autostart': 'True'
       }.items()
   )


   # Configuration RViz
   rviz_config_file = PathJoinSubstitution([
       FindPackageShare('my_robot_navigation'),
       'rviz',
       'nav2.rviz'
   ])


   # Node de transformation de pose ORB-SLAM3 vers Nav2
   pose_transformer_node = Node(
       package='my_robot_navigation',
       executable='pose_transformer',
       name='pose_transformer',
       parameters=[{
           'use_sim_time': use_sim_time
       }],
       remappings=[
           ('/orb_slam3/camera_pose', '/orb_slam3/camera_pose'),
           ('/amcl_pose', '/amcl_pose')
       ],
       output='screen'  # Pour debug
   )


   # RViz node
   rviz_node = Node(
       package='rviz2',
       executable='rviz2',
       name='rviz2',
       output='screen',
       arguments=['-d', rviz_config_file],
       parameters=[{'use_sim_time': use_sim_time}]
   )


   return LaunchDescription([
       declare_use_sim_time_cmd,
       declare_map_yaml_cmd,
       declare_params_file_cmd,
       nav2_bringup,
       pose_transformer_node,
       rviz_node,
   ])
