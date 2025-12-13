import cv2
import time
import json
import UART
import vision

with open('config/config.json', 'r') as f:
    config = json.load(f)

team_color = config["team_color"]
camera_id = config["camera"]["device_id"]

first_grab = True
cmd = "0"

cap = cv2.VideoCapture(camera_id)
if not cap.isOpened():
    print(f"摄像头 {camera_id} 打开失败")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print(f"队伍: {team_color}, 开始!!!!!!!!!!!!")
print("等待电控指令.........................................")

try:
    while True:
        cmd = UART.read_ecu_command()
        print(f"收到指令: cmd={cmd}")
        ret, frame = cap.read()
        if not ret:
            print("读取帧失败")
            time.sleep(0.1)
            break
        frame = cv2.flip(frame, 0)

        target_found = False

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
                print(f"找到红球(安全区已排除): dx={dx}, dy={dy}, dist={dist}")

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
                print(f"找到蓝球(安全区已排除): dx={dx}, dy={dy}, dist={dist}")

        elif cmd == "3":
            centers = vision.find_safe_zones(frame, "red")
            if centers:
                x, y = centers[0]
                dx, dy = vision.calculate_offset(x, y)
                UART.send_data(dx, dy, 0)
                time.sleep(0.1)
                target_found = True
                print(f"找到红安全区: dx={dx}, dy={dy}")
            if first_grab:
                first_grab = False
                print("第一次抓取完成，切换到多目标识别模式")
        elif cmd == "4":
            centers = vision.find_safe_zones(frame, "blue")
            if centers:
                x, y = centers[0]
                dx, dy = vision.calculate_offset(x, y)
                UART.send_data(dx, dy, 0)
                time.sleep(0.1)
                target_found = True
                print(f"找到蓝安全区: dx={dx}, dy={dy}")
            if first_grab:
                first_grab = False
                print("第一次抓取完成，切换到多目标识别模式")

        elif not first_grab:
            # 多色球识别
            colors_to_check = ["red", "blue", "yellow", "black"]
            for color in colors_to_check:
                if color in ["red", "blue"]:
                    
                    balls = vision.find_balls(frame, color)
                else:
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

        if not target_found:
            UART.send_no_target()
            time.sleep(0.1)
            print("未找到目标")

except KeyboardInterrupt:
    print("\n用户中断")
except Exception as e:
    print(f"程序出错: {e}")
    import traceback
    traceback.print_exc()
finally:
    cap.release()
    UART.close_serial()
    print("程序结束")