import cv2
import sys
import os
import numpy as np

# 添加src目录到Python路径，以便导入vision模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import vision

def main():
    # 配置参数
    camera_id = 0  # 摄像头ID
    frame_width = 640
    frame_height = 480
    flip_image = True  # 是否翻转图像（解决画面倒置问题）
    flip_mode = 0  # 翻转模式：0=垂直翻转（上下颠倒）, 1=水平翻转（左右颠倒）, -1=垂直和水平翻转
    
    # 初始化摄像头
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"摄像头 {camera_id} 打开失败")
        return
    
    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
    print("开始测试安全区识别")
    print("按 'q' 退出")
    print("按 '1' 切换到红色安全区检测")
    print("按 '2' 切换到蓝色安全区检测")
    print("按 '3' 同时检测两种安全区")
    
    current_mode = 3  # 默认同时检测两种安全区
    
    try:
        while True:
            # 读取摄像头图像
            ret, frame = cap.read()
            if not ret:
                print("读取帧失败")
                break
            
            # 翻转图像（解决画面倒置问题）
            if flip_image:
                frame = cv2.flip(frame, flip_mode)
            
            # 生成紫色围栏掩码
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            purple_config = vision.load_color("purple")
            lower_purple = np.array(purple_config["lower"])
            upper_purple = np.array(purple_config["upper"])
            mask_purple = cv2.inRange(hsv, lower_purple, upper_purple)
            
            # 形态学操作
            kernel = np.ones((5, 5), np.uint8)
            mask_purple = cv2.morphologyEx(mask_purple, cv2.MORPH_CLOSE, kernel)
            
            # 创建用于显示的掩码图像
            mask_display = cv2.cvtColor(mask_purple, cv2.COLOR_GRAY2BGR)
            
            # 检测安全区
            safe_zones = []
            
            if current_mode in [1, 3]:
                # 检测红色安全区
                red_safe_zone = vision.find_safe_zone(frame, "red")
                if red_safe_zone:
                    safe_zones.append((red_safe_zone, "red"))
                    
            if current_mode in [2, 3]:
                # 检测蓝色安全区
                blue_safe_zone = vision.find_safe_zone(frame, "blue")
                if blue_safe_zone:
                    safe_zones.append((blue_safe_zone, "blue"))
            
            # 在原始画面上标记安全区
            for (x, y), color in safe_zones:
                color_bgr = (0, 0, 255) if color == "red" else (255, 0, 0)
                cv2.circle(frame, (x, y), 10, color_bgr, -1)
                cv2.putText(frame, f"{color} safe zone", (x - 60, y - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_bgr, 2)
                
                # 在掩码图像上也标记安全区
                cv2.circle(mask_display, (x, y), 10, color_bgr, -1)
            
            # 显示图像
            cv2.imshow("摄像头画面 - 安全区检测", frame)
            cv2.imshow("紫色围栏掩码", mask_display)
            
            # 处理按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('1'):
                current_mode = 1
                print("切换到红色安全区检测模式")
            elif key == ord('2'):
                current_mode = 2
                print("切换到蓝色安全区检测模式")
            elif key == ord('3'):
                current_mode = 3
                print("切换到同时检测两种安全区模式")
                
    except KeyboardInterrupt:
        print("用户中断")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("程序结束")

if __name__ == "__main__":
    main()