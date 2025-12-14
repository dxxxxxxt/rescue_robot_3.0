import cv2
import numpy as np
import json
import os

# 精度缩放因子，用于在 trackbar 中表示两位小数（0.01）
SCALE = 100  # 两位小数精度

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
window_name = '蓝色小球阈值调整'
cv2.namedWindow(window_name)

# 针对蓝色小球的优化初始值（浮点，支持两位小数）
initial_values = {
    'H Min': 90.00,     # 蓝色范围下限
    'S Min': 100.00,    # 较高饱和度下限
    'V Min': 100.00,    # 较高亮度下限
    'H Max': 120.00,    # 蓝色范围上限
    'S Max': 255.00,    # 饱和度上限
    'V Max': 255.00     # 亮度上限
}

# 创建滑动条（在 trackbar 中存储为整数：值 * SCALE）
cv2.createTrackbar('H Min', window_name, int(initial_values['H Min'] * SCALE), int(179 * SCALE), lambda x: None)
cv2.createTrackbar('S Min', window_name, int(initial_values['S Min'] * SCALE), int(255 * SCALE), lambda x: None)
cv2.createTrackbar('V Min', window_name, int(initial_values['V Min'] * SCALE), int(255 * SCALE), lambda x: None)
cv2.createTrackbar('H Max', window_name, int(initial_values['H Max'] * SCALE), int(179 * SCALE), lambda x: None)
cv2.createTrackbar('S Max', window_name, int(initial_values['S Max'] * SCALE), int(255 * SCALE), lambda x: None)
cv2.createTrackbar('V Max', window_name, int(initial_values['V Max'] * SCALE), int(255 * SCALE), lambda x: None)

def get_trackbar_float(name):
    """读取 trackbar 的浮点值（两位小数）"""
    return cv2.getTrackbarPos(name, window_name) / SCALE

def save_thresholds():
    """保存阈值配置（保存为保留两位小数的浮点数）"""
    thresholds = {
        'H Min': round(get_trackbar_float('H Min'), 2),
        'S Min': round(get_trackbar_float('S Min'), 2),
        'V Min': round(get_trackbar_float('V Min'), 2),
        'H Max': round(get_trackbar_float('H Max'), 2),
        'S Max': round(get_trackbar_float('S Max'), 2),
        'V Max': round(get_trackbar_float('V Max'), 2)
    }
    
    config_file = os.path.join(config_dir, "hsv_thresholds_blue.json")
    with open(config_file, 'w') as f:
        json.dump(thresholds, f, indent=2)
    print(f"阈值配置已保存到: {config_file}")

def load_thresholds():
    """加载阈值配置（支持浮点两位小数）"""
    config_file = os.path.join(config_dir, "hsv_thresholds_blue.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                thresholds = json.load(f)
            
            for key, value in thresholds.items():
                # value 为浮点，乘 SCALE 并转为 int 设置回 trackbar
                try:
                    cv2.setTrackbarPos(key, window_name, int(round(float(value) * SCALE)))
                except Exception:
                    # 如果某个值无法设置，忽略并继续
                    pass
            print("已加载保存的阈值配置")
            return True
        else:
            print("无保存的配置，使用优化初始值")
            print("提示：蓝色检测主要关注 H Min 和 H Max 参数")
            return False
    except Exception as e:
        print(f"加载配置失败: {e}")
        return False

def print_thresholds():
    """打印当前阈值（保留两位小数）"""
    h_min = get_trackbar_float('H Min')
    s_min = get_trackbar_float('S Min')
    v_min = get_trackbar_float('V Min')
    h_max = get_trackbar_float('H Max')
    s_max = get_trackbar_float('S Max')
    v_max = get_trackbar_float('V Max')
    
    print(f"当前HSV阈值:")
    print(f"Lower: [{h_min:.2f}, {s_min:.2f}, {v_min:.2f}]")
    print(f"Upper: [{h_max:.2f}, {s_max:.2f}, {v_max:.2f}]")

# 加载保存的配置
load_thresholds()

print("使用说明:")
print("- 主要调整 'H Min' 和 'H Max' 参数：控制蓝色范围(90-120)")
print("- 'S Min' 和 'V Min'：提高值可减少环境干扰")
print("- 按 's' 保存配置")
print("- 按 'p' 打印当前阈值") 
print("- 按 'q' 退出")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # 获取当前阈值（浮点，两位小数）
    h_min = get_trackbar_float('H Min')
    s_min = get_trackbar_float('S Min')
    v_min = get_trackbar_float('V Min')
    h_max = get_trackbar_float('H Max')
    s_max = get_trackbar_float('S Max')
    v_max = get_trackbar_float('V Max')

    # HSV颜色空间转换和阈值处理
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # cv2.inRange 需要整数阈值（uint8），这里将浮点值四舍五入为整数
    lower = np.array([int(round(h_min)), int(round(s_min)), int(round(v_min))], dtype=np.uint8)
    upper = np.array([int(round(h_max)), int(round(s_max)), int(round(v_max))], dtype=np.uint8)
    
    mask = cv2.inRange(hsv, lower, upper)
    
    # 形态学去噪
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # 在原图左上角显示当前阈值（保留两位小数）
    cv2.putText(frame, f"H: [{h_min:.2f}-{h_max:.2f}]", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"S: [{s_min:.2f}-{s_max:.2f}]", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"V: [{v_min:.2f}-{v_max:.2f}]", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # 显示结果窗口
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