import cv2
import time
import json
import UART
import vision

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
        elif cmd == "4":
            # 找蓝安全区
            safe_zone = vision.find_safe_zone(frame, "blue")
            balls = []
        else:
            # 自动找己方球
            balls = vision.find_balls(frame, team_color)

        if (cmd in ["1", "2"] or cmd == "0") and balls:
            # 处理小球
            x, y, r = balls[0]
            dx, dy = vision.calculate_offset(x, y)
            dist = vision.calculate_distance(r)
            ball_id = 1 if cmd == "1" or (cmd == "0" and team_color == "red") else 2
            UART.send_data(dx, dy, dist, ball_id)
        elif cmd == "3" and safe_zone:
            # 处理红安全区
            x, y, _ = safe_zone
            dx, dy = vision.calculate_offset(x, y)
            UART.send_data(dx, dy, 0, 5)
        elif cmd == "4" and safe_zone:
            # 处理蓝安全区
            x, y, _ = safe_zone
            dx, dy = vision.calculate_offset(x, y)
            UART.send_data(dx, dy, 0, 6)
        else:
            # 没找到
            UART.send_no_target()
            
        time.sleep(0.1)
            
except KeyboardInterrupt:
    print("\n用户中断")
finally:
    cap.release()
    UART.close_serial()
    print("程序结束")
    
