#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    # Arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
    # RTABMap parameters
    parameters = [
        {
            'frame_id': 'base_footprint',
            'use_sim_time': use_sim_time,
            'subscribe_stereo': True,
            'subscribe_odom': True,
            'subscribe_depth': False,
            'subscribe_rgb': False,
            'subscribe_scan': False,
            
            # Topics de vos caméras stéréo
            'left_image_topic': '/camera/left/left_camera/image_raw',
            'right_image_topic': '/camera/right/right_camera/image_raw',
            'left_camera_info_topic': '/camera/left/left_camera/camera_info',
            'right_camera_info_topic': '/camera/right/right_camera/camera_info',
            'odom_topic': '/odom',
            
            # Fusion avec ORB-SLAM3
            'visual_odometry': False,  # Utiliser l'odométrie externe (ORB-SLAM3)
            'odom_frame_id': 'odom',
            'map_frame_id': 'map',
            'publish_tf': True,
            
            # Paramètres de mapping
            'Rtabmap/TimeThr': '700',
            'Rtabmap/DetectionRate': '1',
            'Rtabmap/CreateIntermediateNodes': 'true',
            'Rtabmap/StartNewMapOnLoopClosure': 'false',
            'Rtabmap/StartNewMapOnGoodSignature': 'false',
            
            # Mémoire et optimisation
            'Mem/RehearsalSimilarity': '0.30',
            'Mem/NotLinkedNodesKept': 'false',
            'Mem/STMSize': '30',
            'Mem/IncrementalMemory': 'true',
            'Mem/InitWMWithAllNodes': 'false',
            
            # Grid map pour navigation 2D
            'Grid/FromDepth': 'false',
            'Grid/3D': 'false',
            'Grid/RangeMax': '10.0',
            'Grid/RangeMin': '0.2',
            'Grid/CellSize': '0.05',  # Résolution de 5cm
            'Grid/MaxObstacleHeight': '2.0',
            'Grid/MaxGroundHeight': '0.0',
            'Grid/MinClusterSize': '10',
            'Grid/MaxGroundAngle': '45',
            'Grid/NormalK': '20',
            'Grid/ClusterRadius': '1.0',
            'Grid/GroundIsObstacle': 'false',
            'Grid/EmptyFloorThreshold': '0.43',
            'Grid/RayTracing': 'true',
            
            # Stéréo
            'Stereo/MaxDisparity': '128.0',
            'Stereo/MinDisparity': '0.0',
            'Stereo/OpticalFlow': 'true',
            'StereoBM/BlockSize': '15',
            'StereoBM/MinDisparity': '0',
            'StereoBM/NumDisparities': '128',
            'StereoBM/PreFilterCap': '31',
            'StereoBM/UniquenessRatio': '15',
            'StereoBM/TextureThreshold': '10',
            'StereoBM/SpeckleWindowSize': '100',
            'StereoBM/SpeckleRange': '4',
            
            # Features detection
            'Kp/MaxFeatures': '400',
            'Kp/DetectorStrategy': '0',  # SURF
            'Kp/NNStrategy': '1',        # kdTree
            'Kp/NndrRatio': '0.8',
            'Kp/MaxDepth': '4.0',
            'Kp/MinDepth': '0.0',
            
            # Visual registration
            'Vis/EstimationType': '1',    # 3D->2D (PnP)
            'Vis/ForwardEstOnly': 'true',
            'Vis/InlierDistance': '0.1',
            'Vis/MinInliers': '15',
            'Vis/Iterations': '300',
            'Vis/RefineIterations': '5',
            'Vis/MaxDepth': '4.0',
            
            # Loop closure
            'LccIcp/Type': '1',          # 2D
            'LccIcp2/CorrespondenceRatio': '0.3',
            'LccBow/MinInliers': '10',
            'LccBow/InlierDistance': '0.02',
        }
    ]
    
    # RTABMap node
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=parameters,
        remappings=[
            ('left/image_rect', '/camera/left/left_camera/image_raw'),
            ('right/image_rect', '/camera/right/right_camera/image_raw'),
            ('left/camera_info', '/camera/left/left_camera/camera_info'),
            ('right/camera_info', '/camera/right/right_camera/camera_info'),
            ('odom', '/odom'),
            ('grid_map', '/map')
        ],
        arguments=['-d']  # Delete database on startup
    )
    
    # RTABMap visualization (optionnel, peut être commenté si pas nécessaire)
    rtabmapviz_node = Node(
        package='rtabmap_viz',
        executable='rtabmap_viz',
        name='rtabmap_viz',
        output='screen',
        parameters=parameters,
        remappings=[
            ('left/image_rect', '/camera/left/left_camera/image_raw'),
            ('right/image_rect', '/camera/right/right_camera/image_raw'),
            ('left/camera_info', '/camera/left/left_camera/camera_info'),
            ('right/camera_info', '/camera/right/right_camera/camera_info'),
            ('odom', '/odom')
        ]
    )
    
    # Map server node pour publier la carte statique (optionnel)
    # Décommentez si vous voulez publier une carte statique en parallèle
    # map_server_node = Node(
    #     package='nav2_map_server',
    #     executable='map_server',
    #     name='map_server',
    #     output='screen',
    #     parameters=[
    #         {'use_sim_time': use_sim_time},
    #         {'yaml_filename': '/path/to/your/saved_map.yaml'}
    #     ]
    # )
    
    return LaunchDescription([
        declare_use_sim_time_cmd,
        rtabmap_node,
        rtabmapviz_node,
        # map_server_node,  # Décommentez si nécessaire
    ])