#!/bin/bash
set -e

# Path setup
WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo " Starting Full Compilation of Workspace   "
echo " Workspace Directory: ${WS_DIR}           "
echo "=========================================="

# 1. Source ROS 2 Environment
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
    echo "[1/4] Sourced ROS 2 Humble environment."
else
    echo "[ERROR] ROS 2 Humble installation not found at /opt/ros/humble/setup.bash"
    exit 1
fi

# 2. Build Livox-SDK2
echo "------------------------------------------"
echo "[2/4] Building Livox-SDK2..."
echo "------------------------------------------"
LIVOX_SDK_DIR="${WS_DIR}/Livox-SDK2"
LIVOX_INSTALL_DIR="${LIVOX_SDK_DIR}/install"

mkdir -p "${LIVOX_SDK_DIR}/build"
cd "${LIVOX_SDK_DIR}/build"
cmake -DCMAKE_INSTALL_PREFIX="${LIVOX_INSTALL_DIR}" ..
make -j$(nproc)
make install

# 3. Build livox_ros_driver2
echo "------------------------------------------"
echo "[3/4] Building livox_ros_driver2..."
echo "------------------------------------------"
LIVOX_DRIVER_DIR="${WS_DIR}/livox_ros_driver2"
cd "${LIVOX_DRIVER_DIR}"
cp -f package_ROS2.xml package.xml
cp -rf launch_ROS2/ launch/

colcon build \
  --cmake-args \
  -DROS_EDITION=ROS2 \
  -DDISTRO_ROS=humble \
  -DLIVOX_LIDAR_SDK_INCLUDE_DIR="${LIVOX_INSTALL_DIR}/include" \
  -DLIVOX_LIDAR_SDK_LIBRARY="${LIVOX_INSTALL_DIR}/lib/liblivox_lidar_sdk_shared.so"

# 4. Build px4_ego and ego_ws
echo "------------------------------------------"
echo "[4/4] Building px4_ego and ego_ws..."
echo "------------------------------------------"
cd "${WS_DIR}/px4_ego"
colcon build

cd "${WS_DIR}/ego_ws"
colcon build

echo "=========================================="
echo " ALL COMPILATIONS COMPLETED SUCCESSFULLY! "
echo "=========================================="
