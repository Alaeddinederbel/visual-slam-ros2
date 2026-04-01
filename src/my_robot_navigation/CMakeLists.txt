cmake_minimum_required(VERSION 3.8)
project(my_robot_navigation)
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
add_compile_options(-Wall -Wextra -Wpedantic)
endif()
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(nav_msgs REQUIRED)



# Add executable
add_executable(pose_transformer src/pose_transformer.cpp)
ament_target_dependencies(pose_transformer
rclcpp
std_srvs
geometry_msgs
tf2
tf2_ros
tf2_geometry_msgs
nav_msgs
)
# Install directories
install(DIRECTORY
config
launch
maps
rviz
logs
DESTINATION share/${PROJECT_NAME}/
)
# Install executables
install(TARGETS
pose_transformer
DESTINATION lib/${PROJECT_NAME}
)

# Install Python scripts
install(PROGRAMS
  src/yolo_detector_node.py
  scripts/object_logger.py
  DESTINATION lib/${PROJECT_NAME}
)
# Installation du package.xml
install(FILES
  package.xml
  DESTINATION share/${PROJECT_NAME}
)


if(BUILD_TESTING)
find_package(ament_lint_auto REQUIRED)
ament_lint_auto_find_test_dependencies()
endif()
ament_package()
