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
        if 31 < area < 1000:   #轮廓面积：可能需要调整
            (x, y), radius = cv2.minEnclosingCircle(cnt)

            # 圆形度检查，确保是近似圆形
            perimeter = cv2.arcLength(cnt, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.7:  # 圆形度阈值，过滤非圆形物体
                    balls.append((int(x), int(y), int(radius)))
    

    return balls

# 寻找安全区

# 安全区识别：
# 1. 检测紫色围栏，当识别到大面积紫色区域时，判断它为安全区
# 2. 检测紫色围栏里面的长方形颜色，当识别到长方形颜色与队伍颜色一致时，判断它为己方安全区

def find_safe_zone(frame, safe_zone_color):
    """检测安全区 - 返回 (x坐标, y坐标)
    safe_zone_color: "red" 或 "blue"，指定要检测的安全区颜色
    """
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
    # 1. 检测紫色围栏
    # 加载紫色（围栏）配置
    purple_config = load_color("purple")
    lower_purple = np.array(purple_config["lower"])
    upper_purple = np.array(purple_config["upper"])
        
    # 创建紫色掩码
    mask_purple = cv2.inRange(hsv, lower_purple, upper_purple)
        
    # 形态学操作 - 闭运算填充缺口
    kernel = np.ones((5, 5), np.uint8)
    mask_purple = cv2.morphologyEx(mask_purple, cv2.MORPH_CLOSE, kernel)
        
    # 寻找紫色围栏轮廓
    contours_purple, _ = cv2.findContours(mask_purple, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
    if contours_purple:
        # 找到最大的紫色区域（围栏）
        largest_purple_contour = max(contours_purple, key=cv2.contourArea)
        purple_area = cv2.contourArea(largest_purple_contour)
            
        if purple_area > 1000:  # 安全区围栏应该有较大面积
            # 创建围栏区域的掩码（只保留围栏内的区域）
            fence_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.drawContours(fence_mask, [largest_purple_contour], -1, 255, -1)
                
            # 2. 检测围栏内的指定颜色区域（红色或蓝色安全区）
            # 加载安全区颜色配置
            color_config = load_color(safe_zone_color)
            lower_color = np.array(color_config["lower"])
            upper_color = np.array(color_config["upper"])
                
            # 创建颜色掩码
            mask_color = cv2.inRange(hsv, lower_color, upper_color)
                
            # 只保留围栏内的颜色区域
            mask_color_inside_fence = cv2.bitwise_and(mask_color, mask_color, mask=fence_mask)
                
            # 形态学操作 - 去除噪声
            mask_color_inside_fence = cv2.morphologyEx(mask_color_inside_fence, cv2.MORPH_OPEN, kernel)
            mask_color_inside_fence = cv2.morphologyEx(mask_color_inside_fence, cv2.MORPH_CLOSE, kernel)
                
            # 寻找颜色区域轮廓
            contours_color, _ = cv2.findContours(mask_color_inside_fence, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
            if contours_color:
                # 找到最大的颜色区域
                largest_color_contour = max(contours_color, key=cv2.contourArea)
                color_area = cv2.contourArea(largest_color_contour)
                    
                # 检查颜色区域是否足够大
                if color_area > 200:  # 可根据实际情况调整
                    # 计算颜色区域的中心点（即安全区中心点）
                    M = cv2.moments(largest_color_contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                            
                        return (cx, cy)  # 只返回两个值：x, y
        
    return None  # 或者返回 (0, 0)
        
    

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

# 距离历史记录，用于平滑滤波
distance_history = []
window_size = 5  # 滑动窗口大小

# 计算目标距离（基于相似三角形原理）
def calculate_distance(ball_radius, camera_fov=60, ball_real_diameter=4.0, focal_length=None):
    """
    通过小球在图像中的大小估算实际距离
    
    参数:
        ball_radius: 小球在图像中的半径(像素)
        camera_fov: 摄像头视野角度(度) - 备用参数
        ball_real_diameter: 小球真实直径(厘米)
        focal_length: 标定的焦距(像素) - 使用你测得的727.8
    """
    
    if ball_radius <= 0:
        return 100  # 默认距离
    
    pixel_diameter = ball_radius * 2
    
    # 优先使用标定的焦距（更准确）
    if focal_length is not None:
        # 使用小孔成像公式：距离 = (实际直径 × 焦距) / 像素直径
        distance = (ball_real_diameter * focal_length) / pixel_diameter
    else:
        # 使用相似三角形原理计算距离
        frame_width = 640  # 图像宽度
        fov_rad = np.radians(camera_fov / 2)  # 视野角度的一半（弧度）
        distance = (ball_real_diameter * frame_width) / (2 * pixel_diameter * np.tan(fov_rad))
    
    return int(distance)

# 距离平滑滤波函数
def smooth_distance(distance):
    """
    使用滑动窗口平均法平滑距离值
    
    参数:
        distance: 当前测量的距离值
    
    返回:
        平滑后的距离值
    """
    global distance_history
    
    # 添加当前距离到历史记录
    distance_history.append(distance)
    
    # 保持历史记录长度不超过窗口大小
    if len(distance_history) > window_size:
        distance_history.pop(0)
    
    # 计算平均值作为平滑后的距离
    if distance_history:
        smoothed_distance = int(np.mean(distance_history))
        return smoothed_distance
    
    return distance



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
    