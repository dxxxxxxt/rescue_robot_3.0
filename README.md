# rescue_robot_3.0
智能救援机器人
这是一个基于OpenCV，使用泰山派，可检测和识别红、黄、蓝、黑四种颜色的小球的机器人视觉识别代码。
目前的策略是机器人看到哪个小球就夹取哪个小球，不分优先级（因为考虑我们是第一次接触这种比赛，所以打算一切按简单的来，不过要是后续有时间，有可能会改为按优先级夹取小球）

比赛分成两种：积分赛+对抗赛
无论是哪种比赛，都是通过抽签决定队伍颜色，然后要防止机器人夹取对方队伍颜色小球，机器人只能夹取自己队伍的小球，黄色小球和黑色小球。其中机器人首次必须自主夹取己方队伍颜色小球，每次夹取黄色小球时只能夹取一个小球，安全区外边有紫色围栏，通过识别紫色围栏然后找到安全区

## 项目结构

```
rescue_vision_2.0/
├── .gitignore
├── README.md
├── .vscode/
├── config/
│   ├── config.json
│   ├── hsv_thresholds_black.json
│   ├── hsv_thresholds_red.json
│   ├── hsv_thresholds_blue.json
│   └── hsv_thresholds_yellow.json
├── src/
│   ├── UART.py
│   ├── main.py
│   ├── vision.py
│   ├── sender.py
│   └── trans.py
└── tests/
    ├── 紫色阈值.py
    ├── 红色阈值.py
    ├── 蓝色阈值.py
    ├── 黄色阈值.py
    └── 黑色阈值.py
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

## 注意事项
1. 串口通信模块需要根据实际情况进行修改，如串口名称、波特率等
2. 视觉处理模块需要根据实际情况进行修改，如视频源、颜色阈值等
3. 运行前确保所有硬件连接正确
4. 记得查看一下摄像头设备索引，有时候会改变