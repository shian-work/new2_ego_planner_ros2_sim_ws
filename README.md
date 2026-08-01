# new2_ego_planner_ros2_sim_ws 修改與設定備忘錄 (REMIND)

本文件紀錄 `~/new2_ego_planner_ros2_sim_ws` 工作區中，關於 **Gazebo 模擬環境 (World/SDF)、無人機載具、雷達點雲橋接、Ego-Planner 轉換流程、系統啟動指令、飛行模式與訂閱節點修改** 的完整說明。

感謝以下這些網址供我慘考
1.download form these git

1.1 px4+ QCcontral（ros2) 

https://github.com/nikhilsnayak/ROS2-PX4

qc 

wget https://github.com/mavlink/qgroundcontrol/releases/download/v4.4.0/QGroundControl.AppImage -O QGroundControl.AppImage

1.2 ego-planner swam

 https://github.com/DongnanHu6556/ego-swarm-ros2/tree/main

1.3 ego-planner-ros2-sim

 https://github.com/DongnanHu6556/ego-planner-ros2- sim/tree/main

1.4 px4_ego 

https://github.com/DongnanHu6556/px4_ego/tree/main

1.5 mid 360驅動

git clone https://github.com/Livox-SDK/Livox-SDK2.git
```
git clone https://github.com/Livox-SDK/livox_ros_driver2.git


## 1. 工作區架構概覽 (Workspace Overview)

* **工作區路徑**：`/home/yu/new2_ego_planner_ros2_sim_ws`
* **主要目錄組件**：
  * `ego-planner-ros2-sim/`：Gazebo SITL 模擬與橋接啟動腳本。
  * `ego_ws/`：Ego-Planner ROS 2 規劃器核心功能包 (包含 `plan_env`, `ego_planner` 等)。
  * `px4_ego/`：PX4 通信與代理控制套件。
  * `livox_ros_driver2/`：Livox 實機驅動 (備用/實機測試)。
  * `PX4-Autopilot/`：PX4 SITL 固件。

---

## 2. 城市/模擬地圖與環境修改 (Environment & World Modifications)

### 2.1 世界檔修改 (`ego.sdf` & `forest2.sdf`)
* **位置**：`~/new2_ego_planner_ros2_sim_ws/ego-planner-ros2-sim/`
* **修改重點**：
  1. 放置圓柱體、建築物及障礙物模型，建立具有空間感與路徑規劃考驗的城市/森林模擬場景。
  2. 調整各模型之姿態 `<pose>`（例如設定 `3.14159` 弧度對齊座標系）與 `<collision>` 幾何體。
* **啟動地圖預設**：
  * 修改 `simulation-gazebo` 檔案中的預設參數： `--world forest2`（或根據需求指定 `--world ego`）。

---

## 3. 無人機載具與雷達配置 (UAV & Mid-360 Sensor Setup)

### 3.1 啟動檔修改 (`px4_sitl_ros2.launch.py`)
* **位置**：`~/new2_ego_planner_ros2_sim_ws/ego-planner-ros2-sim/px4_sitl_ros2.launch.py`
* **修改內容**：
  1. **機型替換**：將原先預設的深度相機模型 `gz_x500_depth` 修改為搭載 Livox Mid-360 3D 固態雷達的模型 **`x500_mid360`**。
  2. **生成起點姿態**：設定 `PX4_GZ_MODEL_POSE` 參數：
     ```python
     'PX4_GZ_MODEL_POSE': '-15,-15,0.1,0,0,3.14159265'
     ```
  3. **Gazebo 話題橋接 (ros_gz_bridge)**：
     將 Gazebo 輸出的點雲話題 `/livox/points/points` 橋接並映射 (remap) 為 ROS 2 話題 `/livox/points_raw`。

---

## 4. 點雲處理與座標轉接流程 (`CustomMsg` vs `PointCloud2`)

### 4.1 轉接腳本 (`lidar_gz_bridge.py`)
* **位置**：`~/new2_ego_planner_ros2_sim_ws/ego-planner-ros2-sim/lidar_gz_bridge.py`
* **作用與邏輯**：
  1. **訂閱點雲**：訂閱 Gazebo 雷達產生的 `sensor_msgs/msg/PointCloud2` 原始點雲 (`/livox/points` 或 `/livox/points_raw`)。
  2. **姿態轉換 (Deskew/Transform)**：訂閱 MAVROS 里程計 (`/mavros/local_position/odom`)，利用機體位置與四元數姿態矩陣將點雲從 Body 座標系動態轉換至全域 `map` 座標系。
  3. **發布至規劃器**：將轉換後的 `PointCloud2` 發布至 **`/grid_map/cloud`**，同時備份發布至 `/livox/lidar` 與 `/lidar_points` 供 RViz 顯示。

### 4.2 點雲格式使用說明 Summary
* **Ego-Planner 端 (`grid_map.cpp`)**：
  * Ego-Planner 直接訂閱 **`sensor_msgs/msg/PointCloud2`** 格式的 `/grid_map/cloud` 話題來建立 Occupancy Grid Map。
* **Livox `CustomMsg` vs `PointCloud2`**：
  * 在模擬中：Gazebo 透過 `lidar_gz_bridge.py` 將點雲轉成全域 `PointCloud2` 送給 `grid_map`。
  * 在實機中：可由 `livox_ros_driver2` 設定 `xfer_format = 0` 直接發布 `PointCloud2`，或由 FAST-LIO 接收 `CustomMsg` 後發布已對齊的 `PointCloud2` (`/cloud_registered`) 給 Ego-Planner。

---

## 5. 編譯與環境加載指令 (Build & Setup Commands)

### 5.1 環境加載
```bash
source ~/new2_ego_planner_ros2_sim_ws/setup_env.bash
```

### 5.2 全局編譯
```bash
cd ~/new2_ego_planner_ros2_sim_ws
./build_all.sh
```

---

## 6. 完整系統啟動指令 (Complete System Launch Commands)

執行模擬與規劃任務時，請依次開啟不同終端機 (Terminal) 執行下列步驟：

### 【步驟一】載入環境變數（每個終端機皆需執行）
```bash
source ~/new2_ego_planner_ros2_sim_ws/setup_env.bash
```

### 【步驟二】啟動 PX4 SITL & Gazebo 模擬器與雷達橋接
```bash
ros2 launch ~/new2_ego_planner_ros2_sim_ws/ego-planner-ros2-sim/px4_sitl_ros2.launch.py
```
*(此指令會自動啟動 Gazebo 模擬環境、PX4 `x500_mid360` 飛控、Micro XRCE Agent、MAVROS 以及雷達橋接 `lidar_gz_bridge.py`)*

### 【步驟三】啟動 PX4 控制代理 (Offboard Control)
* **終端機 3-A（運行 Offboard 控制節點）**：
  ```bash
  ros2 run px4_ego_py offboard_control_test
  ```
* **終端機 3-B（鍵盤控制終端 `mode_key.py`）**：
  ```bash
  cd ~/new2_ego_planner_ros2_sim_ws/px4_ego
  python3 mode_key.py
  ```
  * **按鍵指令說明**：
    * **`t`**：發送起飛指令 (Takeoff)，無人機自動起飛並懸停在指定高度。
    * **`o`**：切換為 **Offboard 離板模式** (Offboard Control Mode)，等待接收 Ego-Planner 發出的軌跡。
    * **`s`**：**自動發送預設目標點** 至東北角座標點 `(15.0, 15.0)` (Send goal pose command to top-right corner)。
    * **`l`**：發送降落指令 (Land control)。
    * **`p`**：切換為位置控制模式 (Position control mode)。
    * **`m`**：切換為手動控制模式 (Manual control mode)。

### 【步驟四】啟動 Ego-Planner 規劃器與 RViz
```bash
ros2 launch ego_planner single_uav_gazebo.launch.py
```
*(啟動 `ego_planner` 節點、地圖建構與 RViz 可視化畫面)*

### 【步驟五】發布目標點
* **方式 A（在 RViz 中點擊）**：在彈出的 RViz 視窗上方工具列選擇 **`2D Goal Pose`**，在地圖上點擊滑鼠右鍵並拖曳方向。
* **方式 B（使用鍵盤指令 `s`）**：在 `mode_key.py` 終端機中輸入 **`s`** 並按 Enter，無人機即會自動規劃軌跡飛往指定目標點。

---

## 7. 如何修改指定飛行目標位置 (How to Change Designated Target Pose)

若要變更鍵盤 `s` 按鍵預設觸發的指定目標位置（例如從 `(15.0, 15.0)` 改為其他座標）：

### 7.1 修改按鍵 `s` 的目標座標 (`offboard_control_test.py`)
1. **開啟檔案**：
   `~/new2_ego_planner_ros2_sim_ws/px4_ego/src/px4_ego_py/px4_ego_py/offboard_control_test.py`
2. **尋找 `mode_cmd_callback` 函式**（約第 142~151 行）：
   ```python
   def mode_cmd_callback(self, msg):
       if msg.data == 's':
           goal_msg = PoseStamped()
           goal_msg.header.stamp = self.get_clock().now().to_msg()
           goal_msg.header.frame_id = 'world'
           goal_msg.pose.position.x = 15.0  # <--- 修改你的指定 X 座標
           goal_msg.pose.position.y = 15.0  # <--- 修改你的指定 Y 座標
           goal_msg.pose.position.z = 1.0   # <--- 修改飛行目標高度 Z
           goal_msg.pose.orientation.w = 1.0
           self.goal_pub.publish(goal_msg)
           self.get_logger().info('Published goal pose to target position!')
           self.control_mode = 'o'
   ```
3. **重新編譯 `px4_ego` 套件**：
   ```bash
   cd ~/new2_ego_planner_ros2_sim_ws/px4_ego
   colcon build
   source install/setup.bash
   ```

### 7.2 修改 Launch 檔中的預設巡航航點 (`single_uav_gazebo.launch.py`)
1. **開啟檔案**：
   `~/new2_ego_planner_ros2_sim_ws/ego_ws/src/ego-swarm-ros2/planner/ego_planner/launch/single_uav_gazebo.launch.py`
2. **尋找 `point0_x`, `point0_y`, `point0_z` 參數**（約第 101~120 行）：
   ```python
   'point0_x': str(15.0), # <--- 修改目標點 0 的 X 座標
   'point0_y': str(0.0),  # <--- 修改目標點 0 的 Y 座標
   'point0_z': str(1.0),  # <--- 修改目標點 0 的 Z 座標
   ```
3. **重新編譯 `ego_ws` 套件**：
   ```bash
   cd ~/new2_ego_planner_ros2_sim_ws/ego_ws
   colcon build --packages-select ego_planner
   ```

---

## 8. Ego-Planner 飛行模式與訂閱節點修改說明 (Flight Modes & Topic Subscriptions)

### 8.1 飛行模式說明 (`flight_type`)
Ego-Planner 狀態機 (`ego_replan_fsm.cpp`) 支援多種飛行模式，由 Launch 檔中的 `flight_type` 參數控制：
* **修改檔案**：`ego_ws/src/ego-swarm-ros2/planner/ego_planner/launch/single_uav_gazebo.launch.py` （預設設定 `'flight_type': str(1)`）
* **模式列舉定義 (`ego_replan_fsm.h`)**：
  * **`flight_type = 1` (MANUAL_TARGET - 手動/動態指定目標模式)**【本專案採用】：
    * 狀態機進入 `WAIT_TARGET` 狀態，等待外部輸入目標點。
    * 可隨時透過 RViz `2D Goal Pose` 或鍵盤 `s` 發送 `geometry_msgs/msg/PoseStamped` 給規劃器，即時重新規劃動態避障軌跡。
  * **`flight_type = 2` (PRESET_TARGET - 預設多航點自動巡航模式)**：
    * 規劃器自動讀取 Launch 中預設的 `point0`, `point1`...`pointN` 航點序列，無須人工手動發送目標點，自動進行多點連續巡航。
  * **`flight_type = 3` (REFENCE_PATH - 參考路徑引導模式)**：
    * 接收全局參考路徑引導無人機飛行。

### 8.2 關鍵訂閱節點與話題 (Subscribed Topics & Remappings)
在 `ego_planner` 節點中，關鍵的訂閱話題及其修改/重映射位置如下：

1. **目標點話題 (`waypoint_sub_`)**
   * **消息類型**：`geometry_msgs/msg/PoseStamped`
   * **訂閱話題**：`/move_base_simple/goal` (或 `/goal_pose`)
   * **作用**：當 `flight_type=1` 時，接收目標點並觸發軌跡生成。
2. **無人機里程計話題 (`odom_sub_`)**
   * **消息類型**：`nav_msgs/msg/Odometry`
   * **訂閱話題**：`/mavros/local_position/odom`
   * **設定檔**：`advanced_param.launch.py` 中的 `odometry_topic` 參數。
   * **作用**：提供無人機當前即時位置與速度姿態給 Ego-Planner 狀態機與軌跡優化器。
3. **點雲地圖話題 (`indep_cloud_sub_`)**
   * **消息類型**：`sensor_msgs/msg/PointCloud2`
   * **內部話題**：`grid_map/cloud` (在 launch 檔重映射為 `cloud_topic` 參數，即 `/lidar_points`)
   * **代碼位置**：`ego_ws/src/ego-swarm-ros2/planner/plan_env/src/library/grid_map.cpp` (約第 170 行)
   * **作用**：提供避障點雲給 `GridMap` 模組，用於建立與更新三維柵格佔用地圖 (Occupancy Grid Map)。

---

### 【補充】實機雷達啟動指令 (Livox Hardware Driver)
若連接實體 Livox Mid-360 雷達測試：
```bash
ros2 launch livox_ros_driver2 rviz_MID360_launch.py
```

---

*備忘錄建置時間：2026-08-01*
