# rescue_robot_3.0
智能救援机器人
这是一个基于OpenCV，使用泰山派，可检测和识别红、黄、蓝、黑四种颜色的小球的机器人视觉识别代码。
目前的策略是机器人看到哪个小球就夹取哪个小球，不分优先级（因为考虑我们是第一次接触这种比赛，所以打算一切按简单的来，不过要是后续有时间，有可能会改为按优先级夹取小球）

主要识别思路：
小车启动,此时电控会发小球和安全区，接收电控发的数据,1为红色小球,2为蓝色小球,3为红色安全区,4为蓝色安全区,
根据电控发的数据判断现在小车要发送什么数据,当识别到目标时发送坐标,如果没有识别到就一直发0,
当first_grab = False时,识别到哪个小球就发送哪个小球坐标,此时电控只发安全区,等待电控指令，
当电控发送数据时,开始识别安全区并返回安全区坐标给电控,小球到达安全区后又开始识别小球。

## 项目结构

```
rescue_vision_3.0/
└── rescue_robot_3.0/
    ├── .gitignore
    ├── README.md
    ├── config/
    │   ├── config.json
    │   ├── hsv_thresholds_black.json
    │   ├── hsv_thresholds_red.json
    │   ├── hsv_thresholds_blue.json
    │   ├── hsv_thresholds_yellow.json
    │   └── hsv_thresholds_purple.json
    ├── src/
    │   ├── UART.py
    │   ├── main.py
    │   ├── vision.py
    │   └── sender.py
    ├── test/
    │   ├── debug_area.py
    │   ├── measure_safe_zone.py
    │   ├── 圆形度阈值测试.py
    │   ├── 测量焦距.py
    │   ├── 紫色阈值.py
    │   ├── 红色阈值.py
    │   ├── 红色阈值2.0.py
    │   ├── 蓝色阈值.py
    │   ├── 黄色阈值.py
    │   └── 黑色阈值.py
    ├── local_ball_distance_tester.py
    └── local_distance_tester.py
```

## 配置说明
1. 运行阈值文件，然后会在config目录生成对应颜色的阈值配置文件
2. 主要配置文件为config/config.json，包含：
   - 队伍颜色（red/blue）
   - 摄像头配置：设备ID、宽度、高度
   - 串口配置：端口名称、波特率
3. 颜色阈值配置文件：
   - hsv_thresholds_black.json：黑色小球检测阈值
   - hsv_thresholds_red.json：红色小球检测阈值
   - hsv_thresholds_blue.json：蓝色小球检测阈值
   - hsv_thresholds_yellow.json：黄色小球检测阈值
   - hsv_thresholds_purple.json：紫色围栏检测阈值


## 主要模块功能
1. 串口通信模块（UART.py）
接收电控信号
发送数据包给电控
没有识别到小球时，发送0
2. 视觉处理模块 (vision.py)
视频流捕获与处理
目标球体检测
安全区域检测
位置判断与状态检测
距离计算
3. 主程序 (main.py)
读取电控发的数据，根据数据进行状态判断，并执行相应的操作
4. 本地测试工具 (local_ball_distance_tester.py)
本地测试小球检测功能
实时显示摄像头画面和颜色掩码视频
测量小球距离和偏移量
支持通过show_mask参数控制掩码视频显示
5. 本地距离测试工具 (local_distance_tester.py)
本地测试距离测量功能
6. 安全区测试工具 (local_safe_zone_tester.py)
本地测试安全区识别功能
实时显示摄像头画面和紫色围栏掩码
支持红色安全区和蓝色安全区检测
提供三种检测模式：仅红色、仅蓝色、同时检测
支持键盘快捷键切换检测模式

## 注意事项
1. 串口通信模块需要根据实际情况进行修改，如串口名称、波特率等
2. 视觉处理模块需要根据实际情况进行修改，如视频源、颜色阈值等
3. 运行前确保所有硬件连接正确
4. 记得查看一下摄像头设备索引，有时候会改变