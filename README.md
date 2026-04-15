#   Visual SLAM Pipeline for Autonomous Robotic Navigation

<p align="center">
  <img src="https://img.shields.io/badge/ROS2-Humble-blue?style=for-the-badge&logo=ros&logoColor=white"/>
  <img src="https://img.shields.io/badge/ORB--SLAM3-Feature%20Extraction-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/RTAB--Map-3D%20Mapping-green?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Nav2-Navigation-red?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Gazebo%20Classic-Simulation-purple?style=for-the-badge"/>
</p>

> **Thesis project - LATIS Laboratory**  
> A complete Visual SLAM pipeline enabling a mobile robot to autonomously navigate using vision only, no LiDAR, no GPS.

---

##   Overview

This project presents the design and implementation of a **Visual SLAM (vSLAM) pipeline** for autonomous robotic navigation. The system relies exclusively on **visual perception** to enable a robot to:

- Estimate its **pose** in real time using ORB feature extraction
- Build accurate **2D and 3D maps** of its environment
- **Navigate autonomously** toward user-defined goals

The entire pipeline is built on a **modular ROS2 architecture**, validated in **Gazebo Classic** simulation.

---

##   System Architecture

The pipeline is composed of three tightly integrated modules:

```
Camera Input
     │
     ▼
┌─────────────────┐
│   ORB-SLAM3     │  ──► Pose Estimation (6-DoF)
│  Feature Extrac │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   RTAB-Map      │  ──► 3D Point Cloud + 2D Occupancy Grid
│  3D Mapping     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Nav2 Stack    │  ──► Autonomous Navigation Commands
│  Path Planning  │
└─────────────────┘
```

### Hardware Architecture
- **Chassis & Propulsion** — differential drive mobile base (URDF/XACRO modeled)
- **Visual Perception** — RGB-D / stereo camera (calibrated, configured via `camera_config.yaml`)
- **Control System** — onboard compute running ROS2 nodes

### Software Architecture
- **ROS2 modular node graph** with asynchronous inter-process communication
- **Real-time image processing** with OpenCV
- **Visualization** via RViz2 and Pangolin
- **Spatial transform management** via TF tree

---

##   Project Structure

```
ros2_ws/
└── src/
    ├── my_robot_description/         # Robot URDF model & visualization
    │   ├── config/
    │   │   └── camera_config.yaml
    │   ├── urdf/
    │   │   ├── camera.xacro
    │   │   ├── common_properties.xacro
    │   │   ├── mobile_base_gazebo.xacro
    │   │   └── my_robot.urdf.xacro
    │   ├── rviz/
    │   │   └── urdf_config.rviz
    │   └── launch/
    │       ├── display.launch.py
    │       └── display_launch.xml
    │
    ├── my_robot_bringup/             # Simulation launch & world
    │   ├── config/
    │   │   └── nav2_tf_fix_params.yaml
    │   ├── worlds/
    │   │   └── my_world.world
    │   └── launch/
    │       ├── my_robot_gazebo.launch.py
    │       └── my_robot_gazebo.launch.xml
    │
    └── my_robot_navigation/          # SLAM & navigation configuration
        └── config/
            ├── ekf_config.yaml
            ├── nav2_params.yaml
            └── pose_transformer.yaml
```

---

##   Dependencies

| Tool / Library | Role |
|---|---|
| **ROS2 Humble** | Middleware & communication framework |
| **ORB-SLAM3** | Visual odometry & pose estimation |
| **RTAB-Map** | Loop closure, 3D mapping, 2D grid generation |
| **Nav2** | Path planning & autonomous navigation |
| **Gazebo Classic** | Physics simulation environment |
| **OpenCV** | Real-time image processing |
| **Pangolin** | ORB-SLAM3 visualization |
| **RViz2** | ROS2 data visualization |
| **robot_localization (EKF)** | State estimation |

---

##   Getting Started

### Prerequisites

- Ubuntu 22.04
- ROS2 Humble
- Gazebo Classic 11
- ORB-SLAM3 (built from source with ROS2 wrapper)
- RTAB-Map ROS2 package
- Nav2

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>/ros2_ws

# Install dependencies
rosdep install --from-paths src --ignore-src -r -y

# Build the workspace
colcon build --symlink-install
source install/setup.bash
```

### Launch the Simulation

```bash
# 1. Launch Gazebo with the robot
ros2 launch my_robot_bringup my_robot_gazebo.launch.py

# 2. Launch the vSLAM pipeline (ORB-SLAM3 + RTAB-Map)
ros2 launch my_robot_navigation slam.launch.py

# 3. Launch Nav2 for autonomous navigation
ros2 launch my_robot_navigation navigation.launch.py
```

---

##   Experiments & Results

### Exploration Phase
The robot was teleoperated to explore the simulated environment, during which:
- ORB features were continuously extracted and matched
- RTAB-Map built a **3D point cloud** and projected a **2D occupancy grid**
- The robot trajectory was recorded and visualized as a pose graph

### Autonomous Navigation Phase
After map generation, navigation goals were sent via RViz2. The robot successfully:
- Localized itself within the previously built map
- Planned and followed collision-free paths
- Reached defined objectives autonomously

### System Validation
- **rqt_graph** — confirmed correct ROS2 topic flow between all nodes
- **TF tree** — verified consistency of all spatial transformations

---

##   Challenges

- **ORB-SLAM3 / ROS2 integration** — C++ standalone library required significant adaptation for ROS2 message compatibility and thread management
- **Visual data synchronization** — ensuring all modules operated on coherent, time-aligned data streams
- **Camera calibration** — precise intrinsic/distortion calibration was critical for accurate pose estimation
- **Modular inter-process communication** — designing non-blocking ROS2 node communication required rigorous software architecture
- **RAM constraints** — limited memory required process optimization and task sequencing to maintain real-time performance

---

##   Future Work

- **Object detection with YOLO** : detect and identify objects/persons for assistive or surveillance robotics
- **IoT integration** : remote supervision, real-time alerts, and multi-agent collaboration via an IoT platform
- **Real-world deployment** : transition from simulation to a physical robot to validate robustness under real-world conditions

---

##   Keywords

`Robotic Navigation` · `Visual Perception` · `Visual SLAM` · `ROS2` · `Localization` · `Mapping` · `ORB-SLAM3` · `RTAB-Map` · `Nav2` · `Gazebo Classic`

---

##   Author

**Ala Eddine Derbel**  
*Embedded Systems Engineer*,
Thesis carried out at **LATIS Laboratory**  

---
