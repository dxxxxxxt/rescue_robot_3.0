import cv2
import numpy as np
import json

# 加载颜色配置
def load_color(color_name):
    try:
        with open(f'config/hsv_thresholds_{color_name}.json', 'r') as f:
            config = json.load(f)
            # 转换格式
            lower = [config["H Min"], config["S Min"], config["V Min"]]
            upper = [config["H Max"], config["S Max"], config["V Max"]]
            return {"lower": lower, "upper": upper}
    except:
        print(f"找不到 {color_name} 的配置文件")
        return {"lower": [0,0,0], "upper": [180,255,255]}

# 检测颜色小球
def find_balls(frame, color_name):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    color_config = load_color(color_name)
    
    lower = np.array(color_config["lower"])
    upper = np.array(color_config["upper"])
    mask = cv2.inRange(hsv, lower, upper)

    # 形态学操作，去除噪声
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    balls = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 100 < area < 1000:   #轮廓面积：可能需要调整
            (x, y), radius = cv2.minEnclosingCircle(cnt)

            # 圆形度检查，确保是近似圆形
            perimeter = cv2.arcLength(cnt, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.6:  # 圆形度阈值，过滤非圆形物体
                    balls.append((int(x), int(y), int(radius)))
    

    return balls

# 寻找安全区

# 安全区识别：
# 1. 检测紫色围栏，当识别到大面积紫色区域时，判断它为安全区
# 2. 检测紫色围栏里面的长方形颜色，当识别到长方形颜色与队伍颜色一致时，判断它为己方安全区

def find_safe_zone(frame, team_color):
    """
    检测安全区并返回位置信息
    frame: 图像帧
    team_color: 队伍颜色 ("red" 或 "blue")
    返回: (x坐标, y坐标, 安全区类型)
    """
    purple_config = load_color("purple")
    lower = np.array(purple_config["lower"])
    upper = np.array(purple_config["upper"])
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 找到最大的紫色区域作为围栏
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        if area > 500:  # 围栏面积较大
            # 返回安全区中心位置
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                zone_type = 5 if team_color == "red" else 6
                return (cx, cy, zone_type)  # 返回坐标
    return None

# 计算相对图像中心的偏移量
def calculate_offset(x, y, frame_width=640, frame_height=480):
    center_x = frame_width // 2
    center_y = frame_height // 2
    x_offset = x - center_x
    y_offset = y - center_y
    
    # 限制在-128到127范围内（1字节有符号）
    x_offset = max(-128, min(127, x_offset))
    y_offset = max(-128, min(127, y_offset))
    
    return x_offset, y_offset

# 计算目标距离（基于相似三角形原理）
def calculate_distance(ball_radius, camera_fov=60, ball_real_diameter=4.0):
    """
    通过小球在图像中的大小估算实际距离
    ball_radius: 小球在图像中的半径(像素)
    camera_fov: 摄像头视野角度(度)
    ball_real_diameter: 小球真实直径(厘米)
    """
    frame_width = 640  # 图像宽度
    fov_rad = np.radians(camera_fov / 2)
    
    if ball_radius > 0:
        # 小球在图像中的直径(像素)
        pixel_diameter = ball_radius * 2
        # 估算距离(厘米)
        distance = (ball_real_diameter * frame_width) / (2 * pixel_diameter * np.tan(fov_rad))
        return int(distance)
    return 100  # 默认距离

# 显示检测结果
def show_frame(frame, balls, target_ball=None):
    # 绘制图像中心十字线
    h, w = frame.shape[:2]
    cv2.line(frame, (w//2, 0), (w//2, h), (255, 255, 255), 1)
    cv2.line(frame, (0, h//2), (w, h//2), (255, 255, 255), 1)
    
    # 绘制所有检测到的小球
    for (x, y, r) in balls:
        cv2.circle(frame, (x, y), r, (0, 255, 0), 2)
    
    # 绘制当前目标小球
    if target_ball:
        x, y, r = target_ball
        cv2.circle(frame, (x, y), r, (0, 0, 255), 3)
        cv2.putText(frame, "目标", (x, y-30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow('视觉检测', frame)