import cv2
import numpy as np
import json

# 加载颜色配置
# 缓存字典，避免重复加载配置文件
_color_config_cache = {}

def load_color(color_name):
    # 检查缓存中是否已有该颜色的配置
    if color_name in _color_config_cache:
        return _color_config_cache[color_name]
    try:
        import os
        # 使用绝对路径加载配置文件
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', f'hsv_thresholds_{color_name}.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            
            # 检查配置是否为双区间结构
            if "range1" in config and "range2" in config and "common" in config:
                # 双区间结构（适用于红色等跨0°的颜色）
                range1 = {
                    "lower": [config["range1"]["H Min"], config["common"]["S Min"], config["common"]["V Min"]],
                    "upper": [config["range1"]["H Max"], config["common"]["S Max"], config["common"]["V Max"]]
                }
                range2 = {
                    "lower": [config["range2"]["H Min"], config["common"]["S Min"], config["common"]["V Min"]],
                    "upper": [config["range2"]["H Max"], config["common"]["S Max"], config["common"]["V Max"]]
                }
                color_config = {"range1": range1, "range2": range2, "is_double_range": True}
            else:
                # 单区间结构（适用于大多数颜色）
                lower = [config["H Min"], config["S Min"], config["V Min"]]
                upper = [config["H Max"], config["S Max"], config["V Max"]]
                color_config = {"lower": lower, "upper": upper, "is_double_range": False}
        
        # 将配置存入缓存
        _color_config_cache[color_name] = color_config
        return color_config
    except Exception as e:
        print(f"找不到 {color_name} 的配置文件或格式错误: {e}")
        return {"lower": [0,0,0], "upper": [180,255,255], "is_double_range": False}

def create_color_mask(hsv, color_name):
    """
    创建指定颜色的掩码
    """
    color_config = load_color(color_name)
    
    if color_config["is_double_range"]:
        # 双区间处理（如红色）
        lower1 = np.array(color_config["range1"]["lower"])
        upper1 = np.array(color_config["range1"]["upper"])
        mask1 = cv2.inRange(hsv, lower1, upper1)
        
        lower2 = np.array(color_config["range2"]["lower"])
        upper2 = np.array(color_config["range2"]["upper"])
        mask2 = cv2.inRange(hsv, lower2, upper2)
        
        # 合并两个区间的掩码
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        # 单区间处理
        lower = np.array(color_config["lower"])
        upper = np.array(color_config["upper"])
        mask = cv2.inRange(hsv, lower, upper)
    
    return mask

# 检测颜色小球
def find_balls(frame, color_name):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 使用新创建的create_color_mask函数创建掩码
    mask = create_color_mask(hsv, color_name)

    # 形态学操作，去除噪声
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    balls = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # 面积筛选范围放宽，适应远近和方便调试
        if 10 < area :  #放开面积的上限1000
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            perimeter = cv2.arcLength(cnt, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                # 可调试输出
                # print(f"area={area:.1f}, radius={radius:.1f}, circularity={circularity:.2f}")
                # 半径范围和圆形度筛选
                if circularity > 0.75 and 5 < radius :  #放开半径的上限60
                    balls.append((int(x), int(y), int(radius)))
    # 如果检测到多个球，可以选择面积最大的那个返回
    balls = sorted(balls, key=lambda b: b[2], reverse=True)  # 按半径降序排序
    return balls

# 寻找安全区

# 安全区识别：
# 1. 检测紫色围栏，当识别到大面积紫色区域时，判断它为安全区
# 2. 检测紫色围栏里面的长方形颜色，当识别到长方形颜色与队伍颜色一致时，判断它为己方安全区

def find_safe_zones(frame, safe_zone_color=None, min_area=1000):
    """
    先找紫色围栏，再判断围栏内部大面积颜色。
    返回所有符合条件安全区的中心点[(cx,cy), ...]
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # --- 1. 先找紫色围栏 ---  
    purple_mask = create_color_mask(hsv, "purple")
    
    # 形态学操作优化紫色围栏掩码
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    purple_mask = cv2.morphologyEx(purple_mask, cv2.MORPH_CLOSE, kernel)
    purple_mask = cv2.morphologyEx(purple_mask, cv2.MORPH_OPEN, kernel)
    
    # 查找紫色围栏轮廓
    purple_contours, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    centers = []
    
    # 如果没有找到紫色围栏，直接返回空列表
    if not purple_contours:
        return centers
    
    # --- 2. 遍历每个紫色围栏，检查内部区域 ---  
    for purple_cnt in purple_contours:
        purple_area = cv2.contourArea(purple_cnt)
        
        # 过滤过小的紫色围栏
        if purple_area < min_area:
            continue
        
        # 获取紫色围栏的外接矩形
        x, y, w, h = cv2.boundingRect(purple_cnt)
        
        # 确保矩形在图像范围内
        if x < 0 or y < 0 or x + w > frame.shape[1] or y + h > frame.shape[0]:
            continue
        
        # 提取围栏内部区域
        roi = frame[y:y+h, x:x+w]
        if roi.size == 0:
            continue
        
        roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # --- 3. 检测围栏内部的矩形面积 ---  
        # 创建一个空白的掩码，用于标记围栏内部的安全区
        inner_mask = np.zeros_like(roi[:,:,0])
        
        # 检测红色或蓝色安全区（根据safe_zone_color参数）
        if safe_zone_color is None or safe_zone_color == "red":
            red_mask = create_color_mask(roi_hsv, "red")
            inner_mask = cv2.bitwise_or(inner_mask, red_mask)
        
        if safe_zone_color is None or safe_zone_color == "blue":
            blue_mask = create_color_mask(roi_hsv, "blue")
            inner_mask = cv2.bitwise_or(inner_mask, blue_mask)
        
        # 形态学操作优化内部掩码
        inner_mask = cv2.morphologyEx(inner_mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找内部安全区轮廓
        inner_contours, _ = cv2.findContours(inner_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for inner_cnt in inner_contours:
            inner_area = cv2.contourArea(inner_cnt)
            
            # 过滤过小的内部区域
            if inner_area < min_area / 2:
                continue
            
            # 检查轮廓是否近似为矩形
            epsilon = 0.05 * cv2.arcLength(inner_cnt, True)
            approx = cv2.approxPolyDP(inner_cnt, epsilon, True)
            
            # 如果轮廓有4个顶点，且是凸的，则认为是矩形
            if len(approx) >= 4 and len(approx) <= 6 and cv2.isContourConvex(approx):
                # 计算内部安全区的中心点（相对于原始图像）
                M = cv2.moments(inner_cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"]) + x
                    cy = int(M["m01"] / M["m00"]) + y
                    centers.append((cx, cy))
    
    return centers

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
def calculate_distance(ball_radius, camera_fov=60, ball_real_diameter=4.0, focal_length=727.8):
    """
    通过小球在图像中的大小估算实际距离
    
    参数:
        ball_radius: 小球在图像中的半径(像素)
        camera_fov: 摄像头视野角度(度) - 备用参数
        ball_real_diameter: 小球真实直径(厘米)
        focal_length: 标定的焦距(像素) - 727.8
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
    
    # 如果历史记录数量足够，可以去除异常值
    if len(distance_history) >= 3:
        dists = sorted(distance_history)
        # 去除最大最小值（可选，根据实际情况决定是否使用）
        dists_filtered = dists[1:-1]  # 去除最大最小
        smoothed_distance = int(np.mean(dists_filtered))
        return smoothed_distance
    else:
        # 如果数量不足就直接计算平均值
        smoothed_distance = int(np.mean(distance_history))
        return smoothed_distance