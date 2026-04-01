import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    # Définition des paramètres de lancement
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    slam_mode = LaunchConfiguration('slam_mode', default='true')
    map_dir = LaunchConfiguration(
        'map_dir', 
        default=os.path.join(get_package_share_directory('my_robot_navigation'), 'maps')
    )
    map_name = LaunchConfiguration('map_name', default='my_map')
    
    # Paramètre pour augmenter le buffer TF
    tf_buffer_duration = LaunchConfiguration('tf_buffer_duration', default='10.0')
    
    return LaunchDescription([
        # Déclaration des arguments
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulation time'),
        DeclareLaunchArgument('slam_mode', default_value='true', description='Enable SLAM mode (mapping)'),
        DeclareLaunchArgument('map_dir', default_value=map_dir, description='Directory for maps'),
        DeclareLaunchArgument('map_name', default_value=map_name, description='Name of the map'),
        DeclareLaunchArgument('tf_buffer_duration', default_value='10.0', description='TF buffer duration in seconds'),
        
        # Launch the robot description and Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('my_robot_bringup'), 'launch', 'my_robot_gazebo.launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
            }.items(),
        ),
        
        # Launch in SLAM mode (Mapping)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('my_robot_slam'), 'launch', 'slam.launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'tf_buffer_duration': tf_buffer_duration,
            }.items(),
            condition=IfCondition(slam_mode),
        ),
        
        # Launch in navigation mode (Localization + Navigation)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('my_robot_navigation'), 'launch', 'navigation.launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map_dir': map_dir,
                'map': [map_dir, '/', map_name, '.yaml'],
                'tf_buffer_duration': tf_buffer_duration,
            }.items(),
            condition=UnlessCondition(slam_mode),
        ),
        
        # Nœud TF pour corriger les problèmes de transformation
        Node(
            package='tf2_ros',
            executable='buffer_server',
            name='tf_buffer_server',
            parameters=[{'buffer_duration': tf_buffer_duration}],
        ),
    ])