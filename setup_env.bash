#!/bin/bash
# Environment setup for new2_ego_planner_ros2_sim_ws

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source ROS 2 Humble base
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
fi

# Source workspace install packages
if [ -f "${WS_DIR}/ego_ws/install/setup.bash" ]; then
    source "${WS_DIR}/ego_ws/install/setup.bash"
fi

if [ -f "${WS_DIR}/px4_ego/install/setup.bash" ]; then
    source "${WS_DIR}/px4_ego/install/setup.bash"
fi

if [ -f "${WS_DIR}/livox_ros_driver2/install/setup.bash" ]; then
    source "${WS_DIR}/livox_ros_driver2/install/setup.bash"
fi

echo "ROS 2 Environment loaded for ego_planner, px4_ego, and livox_ros_driver2."
