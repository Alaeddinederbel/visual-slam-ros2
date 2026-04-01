import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch.actions import TimerAction


def generate_launch_description():
    # === Launch Arguments === #
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
  #  use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_gui = LaunchConfiguration('use_gui', default='true')
    
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
   # declare_use_rviz = DeclareLaunchArgument(
    #    'use_rviz',
   #     default_value='true',
    #    description='Launch RViz2'
   # )
    
    declare_use_gui = DeclareLaunchArgument(
        'use_gui',
        default_value='true',
        description='Launch joint_state_publisher_gui'
    )

    # === File Paths === #
    pkg_robot_description = FindPackageShare('my_robot_description')
    pkg_robot_bringup = FindPackageShare('my_robot_bringup')


    


    urdf_path = PathJoinSubstitution([
        pkg_robot_description, 'urdf', 'my_robot.urdf.xacro'
    ])

   # rviz_config_path = PathJoinSubstitution([
 #       pkg_robot_bringup, 'rviz', 'urdf_config.rviz'
  #  ])

    world_path = PathJoinSubstitution([
        pkg_robot_bringup, 'worlds', 'world.world'
    ])

    # Chemin vers le fichier de configuration des caméras
    camera_config_path = os.path.join(
        get_package_share_directory('my_robot_description'),
        'config',
        'camera_config.yaml'
    )

    # === Nodes === #
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
            'pause': 'false',
            'extra_gazebo_args': '--ros-args --params-file ' + camera_config_path
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
  #  rviz_node = Node(
    #    package='rviz2',
   #     executable='rviz2',
   #     name='rviz2',
    #    arguments=['-d', rviz_config_path],
   #     parameters=[{'use_sim_time': use_sim_time}],
     #   condition=IfCondition(use_rviz),
     #   output='screen'
  #  )
    orbslam_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('orbslam3_ros2'),
                'launch',
               'stereo.launch.py'
            ])
        ])
    )

    # Commande pour désactiver les transports redondants (sécurité supplémentaire)
    disable_transports = ExecuteProcess(
        cmd=[
            'ros2', 'param', 'set',
            '/camera/left/left_camera',
            'disable_pub_plugins',
            '["compressed", "compressedDepth", "theora"]'
        ],
        shell=True
    )

    disable_transports_right = ExecuteProcess(
        cmd=[
            'ros2', 'param', 'set',
            '/camera/right/right_camera',
            'disable_pub_plugins',
            '["compressed", "compressedDepth", "theora"]'
        ],
        shell=True
    )
    delayed_stereo_slam = TimerAction(
        period=5.0,  # secondes
        actions=[orbslam_node]
)

    return LaunchDescription([
        declare_use_sim_time,
       # declare_use_rviz,
        declare_use_gui,
        robot_state_publisher_node,
        joint_state_publisher_node,
        gazebo_launch,
        spawn_entity_node,
        disable_transports,
        disable_transports_right,
        orbslam_node ,
      #  rviz_node
    ])
