import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition

def generate_launch_description():
    # === Launch Arguments ===
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_gui = LaunchConfiguration('use_gui', default='true')
    
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch RViz2'
    )
    
    declare_use_gui = DeclareLaunchArgument(
        'use_gui',
        default_value='true',
        description='Launch joint_state_publisher_gui'
    )

    # === File Paths ===
    pkg_robot_description = FindPackageShare('my_robot_description')
    pkg_robot_bringup = FindPackageShare('my_robot_bringup')
    #pkg_orbslam3 = get_package_share_directory('orbslam3_ros2')

    urdf_path = PathJoinSubstitution([
        pkg_robot_description, 'urdf', 'my_robot.urdf.xacro'
    ])

    rviz_config_path = PathJoinSubstitution([
        pkg_robot_bringup, 'rviz', 'urdf_config.rviz'
    ])

    world_path = PathJoinSubstitution([
        pkg_robot_bringup, 'worlds', 'world.world'
    ])

    # === ORB-SLAM3 file paths ===
  #  vocab_path = os.path.join(pkg_orbslam3, 'vocabulary', 'ORBvoc.txt')
  #  settings_path = os.path.join(pkg_orbslam3, 'camera', 'stereo_camera.yaml')
   # config_file = os.path.join(pkg_orbslam3, 'config', 'params.yaml')  # Optionnel si utilisé

    #if not os.path.exists(vocab_path):
    #    raise FileNotFoundError(f"ORB Vocabulary file not found at: {vocab_path}")
    #if not os.path.exists(settings_path):
     #   raise FileNotFoundError(f"Camera settings file not found at: {settings_path}")

    # === Nodes ===
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': Command(['xacro ', urdf_path]),
            'use_sim_time': use_sim_time
        }]
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher_gui' if use_gui == 'true' else 'joint_state_publisher',
        executable='joint_state_publisher_gui' if use_gui == 'true' else 'joint_state_publisher',
        condition=IfCondition(use_gui)
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'), 
                'launch', 
                'gazebo.launch.py'
            ])
        ]),
        launch_arguments={
            'world': world_path,
            'verbose': 'false',
            'pause': 'false'
        }.items()
    )

    spawn_entity_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'my_robot',
            '-z', '0.1'
        ],
        output='screen'
    )

  #  orbslam3_node = Node(
   #     package='orbslam3_ros2',
    #    executable='stereo_node',
     #   name='orbslam3',
      #  output='screen',
       # arguments=[vocab_path, settings_path, 'false'],  # Positional args
        #parameters=[config_file],  # Or replace with a dict like before
     #   remappings=[
      #      ('/left/image_raw', '/camera/left/left_camera/image_raw'),
       #     ('/right/image_raw', '/camera/right/right_camera/image_raw'),
        #    ('/left/camera_info', '/camera/left/left_camera/camera_info'),
         #   ('/right/camera_info', '/camera/right/right_camera/camera_info'),
        #]
    #)

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
        output='screen'
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_rviz,
        declare_use_gui,
        robot_state_publisher_node,
        joint_state_publisher_node,
        gazebo_launch,
        spawn_entity_node,
       # orbslam3_node,
        rviz_node
    ])
