#  Visual SLAM Pipeline for Autonomous Robotic Navigation (ROS2)

This repository contains the implementation of a **Visual SLAM (vSLAM) pipeline for autonomous robotic navigation**, developed as an end-of-studies thesis at **LATIS (2024–2025)**.

The project focuses on building a **modular ROS2-based robotic system** capable of autonomous navigation using **visual perception only**, validated in **Gazebo Classic simulation**.

---

#  Project Objective

The goal of this work is to design and implement a robotic system that can:

- Perceive its environment using a monocular camera
- Estimate its pose using visual SLAM
- Build 2D/3D maps of the environment
- Navigate autonomously to defined goals
- Operate in a fully simulated ROS2 + Gazebo environment

---

# 🏗️ System Architecture

The system is built using a **modular ROS2 architecture** composed of multiple packages:
ros2_ws/
└── src/
├── my_robot_description/
│ ├── urdf/
│ ├── config/
│ ├── launch/
│ └── rviz/
│
├── my_robot_bringup/
│ ├── launch/
│ ├── worlds/
│ ├── config/
│ └── rviz/
│
├── my_robot_navigation/
│ ├── config/
│ ├── ekf_config.yaml
│ ├── nav2_params.yaml
│ └── pose_transformer.yaml
│ 
│ 
│ 
---

---

# 🤖 Robot Description

### `my_robot_description`
This package defines the robot model and visualization tools.

- URDF / XACRO robot model
- Camera sensor configuration
- RViz visualization setup
- Robot parameters and properties

  Key files:
- `my_robot.urdf.xacro`
- `camera.xacro`
- `mobile_base_gazebo.xacro`
- `camera_config.yaml`

---

#  Simulation & Bringup

### `my_robot_bringup`
Handles robot execution in simulation.

- Gazebo Classic world integration
- Robot spawn and initialization
- Simulation launch files
- RViz configuration

  Key files:
- `my_robot_gazebo.launch.py`
- `my_world.world`
- `nav2_tf_fix_params.yaml`

---

#   Navigation & SLAM

### `my_robot_navigation`
Handles perception, localization, and navigation.

- EKF sensor fusion (`ekf_config.yaml`)
- Nav2 configuration (`nav2_params.yaml`)
- Pose transformation system
- SLAM integration logic

---

#  Visual SLAM Pipeline

The pipeline integrates:

###   Visual Perception
- Camera stream processing
- OpenCV-based image handling

###   Feature Extraction
- ORB feature detection
- Robust feature matching

###   Localization
- ORB-SLAM3 for pose estimation
- Real-time trajectory tracking

###   Mapping
- RTAB-Map for:
  - 2D occupancy grid
  - 3D point cloud map
  - Loop closure detection

###   Navigation
- ROS2 Nav2 stack
- Path planning
- Obstacle avoidance
- Goal-based navigation

---

#   Simulation Environment

The system is tested in:

- **Gazebo Classic**
- Custom robot world (`my_world.world`)
- RViz for visualization
- ROS2 communication layer

---

#   Technologies Used

- ROS2 (Humble / Foxy depending on setup)
- Gazebo Classic
- ORB-SLAM3
- RTAB-Map
- Nav2 Stack
- OpenCV
- RViz2
- EKF Sensor Fusion

---

#   Results

The system demonstrates:

- Successful visual-based localization
- Accurate 2D and 3D mapping
- Stable trajectory estimation
- Autonomous navigation in simulation
- Robust ROS2 modular architecture

---

#   Key Achievements

✔ Fully modular ROS2 architecture  
✔ Visual-only SLAM navigation system  
✔ Integration of ORB-SLAM3 + RTAB-Map + Nav2  
✔ Real-time simulation in Gazebo  
✔ End-to-end autonomous navigation pipeline  

---

#   Thesis Summary

This thesis, carried out at **LATIS**, focuses on the development of a **Visual SLAM pipeline for autonomous robotic navigation**.

The system enables a robot to navigate using only visual perception by combining:

- ORB-SLAM3 for pose estimation  
- RTAB-Map for mapping  
- Nav2 for autonomous navigation  

Experiments in Gazebo Classic demonstrate that the robot can:
- Explore unknown environments
- Generate accurate 2D/3D maps
- Navigate autonomously to target goals

The results validate the proposed architecture and confirm the feasibility of vision-only robotic navigation systems.

---

#  Future Work

- Deployment on real hardware robot
- Deep learning-based perception improvement
- Better loop closure robustness
- Optimization for embedded systems
- Multi-robot collaboration

---

#  Author
Ala Eddine Derbel - Embedded Systems Engineer
End-of-studies project  
**LATIS – 2024/2025**

---

#  Keywords

Visual SLAM, ROS2, ORB-SLAM3, RTAB-Map, Nav2, Gazebo Classic, Robotic Navigation, Mapping, Localization

