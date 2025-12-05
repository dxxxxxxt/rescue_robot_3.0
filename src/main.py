import cv2
import time
import json
import UART
import vision

"""
小车启动,此时电控会发小球和安全区，接收电控发的数据,1为红色小球,2为蓝色小球,3为红色安全区,4为蓝色安全区,
根据电控发的数据判断现在小车要发送什么数据,当识别到目标时发送坐标,如果没有识别到就一直发0,
当first_grab = False时,识别到哪个小球就发送哪个小球坐标,此时电控只发安全区,等待电控指令，
当电控发送数据时,开始识别安全区并返回安全区坐标给电控,小球到达安全区后又开始识别小球

"""

# 加载配置
with open('config/config.json', 'r') as f:
    config = json.load(f)

team_color = config["team_color"]
camera_id = config["camera"]["device_id"]

#初始化变量
first_grab = True     # 是否是第一次抓取
has_yellow = False    # 是否已经抓了黄球
cmd = "0"

# 初始化摄像头和串口
cap = cv2.VideoCapture(camera_id)

print(f"队伍: {team_color}, 开始!!!!!!!!!!!!")


try:
    while True:
        # 读取电控数据
        cmd_data = UART.read_ecu_command()
        if cmd_data:
                # 假设电控发送的是单个字符，如 "1", "2", "3", "4"
                cmd = cmd_data[0] if cmd_data else "0"
                print(f"收到指令: cmd={cmd}")
    
        ret, frame = cap.read()
        if not ret:
            break
    
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]

        # 重置变量
        balls = []
        safe_zone = None
    
        #识别
        if cmd == "1":
            # 找红球
            balls = vision.find_balls(frame, "red")
        elif cmd == "2":
            # 找蓝球
            balls = vision.find_balls(frame, "blue")
        elif cmd == "3":
            # 找红安全区
            safe_zone = vision.find_safe_zone(frame, "red")
            balls = []
            first_grab = False
        elif cmd == "4":
            # 找蓝安全区
            safe_zone = vision.find_safe_zone(frame, "blue")
            balls = []
            first_grab = False
        else:
            balls = vision.find_balls(frame, "red")
            balls = vision.find_balls(frame, "blue")
            balls = vision.find_balls(frame, "yellow")
            balls = vision.find_balls(frame, "black")

        
        #发送数据
        if (cmd in ["1", "2"] or cmd == "0") and balls:
            # 处理小球
            x, y, r = balls[0]
            dx, dy = vision.calculate_offset(x, y)
            dist = vision.calculate_distance(r)
            UART.send_data(dx, dy, dist)
        elif cmd == "3" and safe_zone:
            # 处理红安全区
            x, y, _ = safe_zone
            dx, dy = vision.calculate_offset(x, y)
            UART.send_data(dx, dy, 0)
        elif cmd == "4" and safe_zone:
            # 处理蓝安全区
            x, y, _ = safe_zone
            dx, dy = vision.calculate_offset(x, y)
            UART.send_data(dx, dy, 0)
        elif first_grab == False:
            #识别哪个就发送哪个
            x, y, r = balls[0]
            dx, dy = vision.calculate_offset(x, y)
            dist = vision.calculate_distance(r)
            UART.send_data(dx, dy, dist)
        else:
            # 没找到
            UART.send_no_target()
            
        
            
except KeyboardInterrupt:
    print("\n用户中断")
finally:
    cap.release()
    UART.close_serial()
    print("程序结束")
    
