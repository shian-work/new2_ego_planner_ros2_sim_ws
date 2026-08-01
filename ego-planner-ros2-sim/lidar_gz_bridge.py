#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import Odometry
from px4_msgs.msg import VehicleLocalPosition
from rclpy.qos import qos_profile_sensor_data, QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
import numpy as np

class LidarBridge(Node):
    def __init__(self):
        super().__init__('lidar_points_transfer')
        
        qos_sub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=10
        )

        # 1. 订阅 MAVROS 里程计
        self.odom_sub = self.create_subscription(
            Odometry,
            '/mavros/local_position/odom',
            self.odom_callback,
            qos_sub
        )

        # 2. 备用：订阅 PX4 内部 VehicleLocalPosition
        self.px4_pos_sub = self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position_v1',
            self.px4_pos_callback,
            qos_sub
        )

        # 3. 订阅 Gazebo 原始 LiDAR 点云 (同时兼容 /livox/points 与 /livox/points_raw)
        self.subscription = self.create_subscription(
            PointCloud2,
            '/livox/points',
            self.cloud_callback,
            qos_profile_sensor_data
        )
        self.subscription_raw = self.create_subscription(
            PointCloud2,
            '/livox/points_raw',
            self.cloud_callback,
            qos_profile_sensor_data
        )

        # 4. 发布给 EGO-Planner (grid_map) 与 RViz 可视化
        self.publisher = self.create_publisher(PointCloud2, '/grid_map/cloud', 10)
        self.livox_pub = self.create_publisher(PointCloud2, '/livox/lidar', 10)
        self.lidar_points_pub = self.create_publisher(PointCloud2, '/lidar_points', 10)

        self.curr_pos = None
        self.curr_rot = None

    def odom_callback(self, msg: Odometry):
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation
        self.curr_pos = np.array([pos.x, pos.y, pos.z])
        
        # 四元数 (w, x, y, z) 转换为 3x3 旋转矩阵
        w, x, y, z = ori.w, ori.x, ori.y, ori.z
        self.curr_rot = np.array([
            [1 - 2*(y**2 + z**2), 2*(x*y - w*z),     2*(x*z + w*y)],
            [2*(x*y + w*z),     1 - 2*(x**2 + z**2), 2*(y*z - w*x)],
            [2*(x*z - w*y),     2*(y*z + w*x),     1 - 2*(x**2 + y**2)]
        ])

    def px4_pos_callback(self, msg: VehicleLocalPosition):
        if self.curr_pos is None or self.curr_rot is None:
            # PX4 NED -> ENU: [y, x, -z]
            self.curr_pos = np.array([msg.y, msg.x, -msg.z])
            heading = msg.heading
            ch = np.cos(heading)
            sh = np.sin(heading)
            self.curr_rot = np.array([
                [ch, -sh, 0.0],
                [sh,  ch, 0.0],
                [0.0, 0.0, 1.0]
            ])

    def cloud_callback(self, msg: PointCloud2):
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"

        if msg.data and len(msg.data) > 0:
            try:
                point_step = msg.point_step
                if point_step >= 12:
                    num_points = len(msg.data) // point_step
                    stride = point_step // 4
                    data = np.frombuffer(msg.data, dtype=np.float32).copy()
                    if len(data) >= num_points * stride:
                        data_matrix = data[:num_points * stride].reshape(num_points, stride)
                        
                        if self.curr_pos is not None and self.curr_rot is not None:
                            xyz_body = data_matrix[:, :3]
                            xyz_odom = (self.curr_rot @ xyz_body.T).T + self.curr_pos
                            data_matrix[:, :3] = xyz_odom

                        msg.data = data_matrix.tobytes()
            except Exception as e:
                pass

        self.publisher.publish(msg)
        self.livox_pub.publish(msg)
        self.lidar_points_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = LidarBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
