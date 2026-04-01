import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    # Paramètres
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    # Chemin vers le fichier de paramètres
    params_file = os.path.join(
        get_package_share_directory('my_robot_bringup'),
        'config',
        'nav2_tf_fix_params.yaml'
    )
    
    return LaunchDescription([
        # Déclaration des arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time if true'
        ),
        
        # Node TF Buffer Server avec une plus grande capacité de buffer
        Node(
            package='tf2_ros',
            executable='buffer_server',
            name='tf_buffer_server',
            parameters=[{'buffer_duration': 60.0, 'use_sim_time': use_sim_time}],
            output='screen'
        ),
        
        # Static Transform Publisher pour les roues - NOTER l'utilisation correcte de use_sim_time
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='wheel_tf_publisher',
            arguments=['-0.075', '0.14', '0.0', '0.0', '0.0', '0.0', '1.0', 'base_link', 'left_wheel_back_link'],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
        
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='wheel_tf_publisher_2',
            arguments=['0.075', '0.14', '0.0', '0.0', '0.0', '0.0', '1.0', 'base_link', 'left_wheel_front_link'],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
        
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='wheel_tf_publisher_3',
            arguments=['-0.075', '-0.14', '0.0', '0.0', '0.0', '0.0', '1.0', 'base_link', 'right_wheel_back_link'],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
        
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='wheel_tf_publisher_4',
            arguments=['0.075', '-0.14', '0.0', '0.0', '0.0', '0.0', '1.0', 'base_link', 'right_wheel_front_link'],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
    ])
