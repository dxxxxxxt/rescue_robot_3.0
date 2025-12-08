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
cmd = "0"  # 初始命令

# 初始化摄像头和串口
cap = cv2.VideoCapture(camera_id)
if not cap.isOpened():
    print(f"摄像头 {camera_id} 打开失败")
    exit(1)

# 设置摄像头参数
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


print(f"队伍: {team_color}, 开始!!!!!!!!!!!!")
print("等待电控指令.........................................")

try:
    while True:
        # 读取电控数据
        cmd = UART.read_ecu_command()
        
        print(f"收到指令: cmd={cmd}")
        
        ret, frame = cap.read()
        
        if not ret:
            print("读取帧失败")
            time.sleep(0.1)
            break
       
        
        # 翻转图像（解决画面倒置问题）
        frame = cv2.flip(frame, 0)  # 0=垂直翻转（上下颠倒）
    
        # 重置变量
        target_found = False
    
        #识别
        if cmd == "1":
            # 找红球
            balls = vision.find_balls(frame, "red")
            if balls:
                x, y, r = max(balls, key=lambda b: b[2])
                dx, dy = vision.calculate_offset(x, y)
                raw_dist = vision.calculate_distance(r)
                dist = vision.smooth_distance(raw_dist)
                UART.send_data(dx, dy, dist)
                time.sleep(0.1)
                target_found = True
                print(f"找到红球: dx={dx}, dy={dy}, dist={dist}")
        elif cmd == "2":
            # 找蓝球
            balls = vision.find_balls(frame, "blue")
            if balls:
                x, y, r = max(balls, key=lambda b: b[2])
                dx, dy = vision.calculate_offset(x, y)
                raw_dist = vision.calculate_distance(r)
                dist = vision.smooth_distance(raw_dist)
                UART.send_data(dx, dy, dist)
                time.sleep(0.1)
                target_found = True
                print(f"找到蓝球: dx={dx}, dy={dy}, dist={dist}")
        elif cmd == "3" :
            # 处理红安全区
            safe_zone = vision.find_safe_zone(frame, "red")  
            if safe_zone:
                x, y = safe_zone  
                dx, dy = vision.calculate_offset(x, y)
                UART.send_data(dx, dy, 0)
                time.sleep(0.1)
                target_found = True
                print(f"找到红安全区: dx={dx}, dy={dy}")
                if first_grab:
                    first_grab = False
                    print("第一次抓取完成，切换到多目标识别模式")
        elif cmd == "4" :
            # 处理蓝安全区
            safe_zone = vision.find_safe_zone(frame, "blue")  
            if safe_zone:
                x, y = safe_zone  
                dx, dy = vision.calculate_offset(x, y)
                UART.send_data(dx, dy, 0)
                time.sleep(0.1)
                target_found = True
                print(f"找到蓝安全区: dx={dx}, dy={dy}")
                if first_grab:
                    first_grab = False
                    print("第一次抓取完成，切换到多目标识别模式")
        elif not first_grab:
            # 尝试识别各种颜色的小球
            colors_to_check = ["red", "blue", "yellow", "black"]
            for color in colors_to_check:
                balls = vision.find_balls(frame, color)
                if balls:
                    x, y, r = max(balls, key=lambda b: b[2])
                    dx, dy = vision.calculate_offset(x, y)
                    raw_dist = vision.calculate_distance(r)
                    dist = vision.smooth_distance(raw_dist)
                    UART.send_data(dx, dy, dist)
                    time.sleep(0.1)
                    target_found = True
                    print(f"识别到{color}色小球: dx={dx}, dy={dy}, dist={dist}")
                    break
        # 没有找到目标时发送无目标信号
        if not target_found:
            UART.send_no_target()
            time.sleep(0.1)
            print("未找到目标")
            
except KeyboardInterrupt:
    print("\n用户中断")
except Exception as e:
    print(f"程序出错: {e}")
    import traceback
    traceback.print_exc()  # 添加了堆栈跟踪
finally:
    cap.release()
    UART.close_serial()
    print("程序结束")
    
