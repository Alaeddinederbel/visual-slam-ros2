#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import sys
import time

class TopicChecker(Node):
    def __init__(self):
        super().__init__('topic_checker')
        self.topic_found = False
        
        # Get list of all topics
        self.topic_list = self.get_topic_names_and_types()
        
        # Look for ORB-SLAM3 camera pose topic
        for topic_name, _ in self.topic_list:
            if topic_name == '/orb_slam3/camera_pose':
                self.get_logger().info(f"ORB-SLAM3 camera pose topic found!")
                self.topic_found = True
                break
        
        if not self.topic_found:
            self.get_logger().error("ORB-SLAM3 camera pose topic NOT found! RTAB-Map will not function properly.")
            self.get_logger().error("Please make sure ORB-SLAM3 is running before launching RTAB-Map.")
            time.sleep(2)  # Give time for the message to be seen

def main():
    rclpy.init()
    checker = TopicChecker()
    
    if not checker.topic_found:
        print("WARNING: ORB-SLAM3 is not running. RTAB-Map requires ORB-SLAM3 for odometry.")
        print("Starting RTAB-Map anyway, but it will not work properly without ORB-SLAM3.")
    else:
        print("ORB-SLAM3 is running. RTAB-Map can proceed normally.")
    
    checker.destroy_node()
    rclpy.shutdown()
    
    # Return exit code based on topic presence
    return 0 if checker.topic_found else 1

if __name__ == '__main__':
    sys.exit(main())
