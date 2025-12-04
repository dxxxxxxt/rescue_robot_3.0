import cv2
import numpy as np
import json
import os

# 配置目录
config_dir = 'config'
os.makedirs(config_dir, exist_ok=True)

# 初始化摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头")
    exit(1)

# 设置摄像头参数
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 创建窗口和滑动条
window_name = '紫色围栏阈值调整'
cv2.namedWindow(window_name)

# 针对紫色围栏的优化初始值
initial_values = {
    'H Min': 125,    # 紫色范围下限
    'S Min': 100,    # 较高饱和度下限
    'V Min': 100,    # 较高亮度下限
    'H Max': 150,    # 紫色范围上限
    'S Max': 255,    # 饱和度上限
    'V Max': 255     # 亮度上限
}

# 创建滑动条
cv2.createTrackbar('H Min', window_name, initial_values['H Min'], 179, lambda x: None)
cv2.createTrackbar('S Min', window_name, initial_values['S Min'], 255, lambda x: None)
cv2.createTrackbar('V Min', window_name, initial_values['V Min'], 255, lambda x: None)
cv2.createTrackbar('H Max', window_name, initial_values['H Max'], 179, lambda x: None)
cv2.createTrackbar('S Max', window_name, initial_values['S Max'], 255, lambda x: None)
cv2.createTrackbar('V Max', window_name, initial_values['V Max'], 255, lambda x: None)

def save_thresholds():
    """保存阈值配置"""
    thresholds = {
        'H Min': cv2.getTrackbarPos('H Min', window_name),
        'S Min': cv2.getTrackbarPos('S Min', window_name),
        'V Min': cv2.getTrackbarPos('V Min', window_name),
        'H Max': cv2.getTrackbarPos('H Max', window_name),
        'S Max': cv2.getTrackbarPos('S Max', window_name),
        'V Max': cv2.getTrackbarPos('V Max', window_name)
    }
    
    config_file = os.path.join(config_dir, "hsv_thresholds_purple.json")
    with open(config_file, 'w') as f:
        json.dump(thresholds, f, indent=2)
    print(f"阈值配置已保存到: {config_file}")

def load_thresholds():
    """加载阈值配置"""
    config_file = os.path.join(config_dir, "hsv_thresholds_purple.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                thresholds = json.load(f)
            
            for key, value in thresholds.items():
                cv2.setTrackbarPos(key, window_name, value)
            print("已加载保存的阈值配置")
            return True
        else:
            print("无保存的配置，使用优化初始值")
            print("提示：紫色检测主要关注 H Min 和 H Max 参数")
            return False
    except Exception as e:
        print(f"加载配置失败: {e}")
        return False

def print_thresholds():
    """打印当前阈值"""
    h_min = cv2.getTrackbarPos('H Min', window_name)
    s_min = cv2.getTrackbarPos('S Min', window_name)
    v_min = cv2.getTrackbarPos('V Min', window_name)
    h_max = cv2.getTrackbarPos('H Max', window_name)
    s_max = cv2.getTrackbarPos('S Max', window_name)
    v_max = cv2.getTrackbarPos('V Max', window_name)
    
    print(f"当前HSV阈值:")
    print(f"Lower: [{h_min}, {s_min}, {v_min}]")
    print(f"Upper: [{h_max}, {s_max}, {v_max}]")

# 加载保存的配置
load_thresholds()

print("使用说明:")
print("- 主要调整 'H Min' 和 'H Max' 参数：控制紫色范围(125-150)")
print("- 'S Min' 和 'V Min'：提高值可减少环境干扰")
print("- 按 's' 保存配置")
print("- 按 'p' 打印当前阈值") 
print("- 按 'q' 退出")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # 获取当前阈值
    h_min = cv2.getTrackbarPos('H Min', window_name)
    s_min = cv2.getTrackbarPos('S Min', window_name)
    v_min = cv2.getTrackbarPos('V Min', window_name)
    h_max = cv2.getTrackbarPos('H Max', window_name)
    s_max = cv2.getTrackbarPos('S Max', window_name)
    v_max = cv2.getTrackbarPos('V Max', window_name)

    # HSV颜色空间转换和阈值处理
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    
    mask = cv2.inRange(hsv, lower, upper)
    
    # 形态学去噪
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # 显示结果
    cv2.imshow('原视频', frame)
    cv2.imshow('掩码', mask)
    cv2.imshow('检测结果', result)

    # 按键处理
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        save_thresholds()
    elif key == ord('p'):
        print_thresholds()

# 清理
cap.release()
cv2.destroyAllWindows()