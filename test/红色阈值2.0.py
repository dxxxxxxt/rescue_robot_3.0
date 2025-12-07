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

# 创建窗口
window_name = '红色小球阈值调整'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 800, 600)

print("=" * 60)
print("红色阈值调整工具")
print("红色在HSV中有两个区间:")
print("区间1: H=0-10 (低值红色)")
print("区间2: H=170-180 (高值红色)")
print("=" * 60)

# 初始化阈值 - 分开两个区间
initial_values = {
    # 区间1: 0-10
    'H1 Min': 0,      # 区间1 H最小值
    'H1 Max': 10,     # 区间1 H最大值
    
    # 区间2: 170-180
    'H2 Min': 170,    # 区间2 H最小值
    'H2 Max': 180,    # 区间2 H最大值
    
    # 饱和度和亮度（两个区间共用）
    'S Min': 100,     # 饱和度最小值
    'V Min': 100,     # 亮度最小值
    'S Max': 255,     # 饱和度最大值
    'V Max': 255      # 亮度最大值
}

# 创建滑动条（分开两个区间）
cv2.createTrackbar('H1 Min', window_name, initial_values['H1 Min'], 179, lambda x: None)
cv2.createTrackbar('H1 Max', window_name, initial_values['H1 Max'], 179, lambda x: None)
cv2.createTrackbar('H2 Min', window_name, initial_values['H2 Min'], 179, lambda x: None)
cv2.createTrackbar('H2 Max', window_name, initial_values['H2 Max'], 179, lambda x: None)
cv2.createTrackbar('S Min', window_name, initial_values['S Min'], 255, lambda x: None)
cv2.createTrackbar('V Min', window_name, initial_values['V Min'], 255, lambda x: None)
cv2.createTrackbar('S Max', window_name, initial_values['S Max'], 255, lambda x: None)
cv2.createTrackbar('V Max', window_name, initial_values['V Max'], 255, lambda x: None)

def save_thresholds():
    """保存阈值配置"""
    thresholds = {
        'range1': {
            'H Min': cv2.getTrackbarPos('H1 Min', window_name),
            'H Max': cv2.getTrackbarPos('H1 Max', window_name)
        },
        'range2': {
            'H Min': cv2.getTrackbarPos('H2 Min', window_name),
            'H Max': cv2.getTrackbarPos('H2 Max', window_name)
        },
        'common': {
            'S Min': cv2.getTrackbarPos('S Min', window_name),
            'V Min': cv2.getTrackbarPos('V Min', window_name),
            'S Max': cv2.getTrackbarPos('S Max', window_name),
            'V Max': cv2.getTrackbarPos('V Max', window_name)
        }
    }
    
    config_file = os.path.join(config_dir, "red_thresholds_v2.json")
    with open(config_file, 'w') as f:
        json.dump(thresholds, f, indent=2)
    print(f"阈值配置已保存到: {config_file}")
    
    # 同时生成Python代码片段
    generate_code_snippet(thresholds)

def generate_code_snippet(thresholds):
    """生成可直接使用的代码片段"""
    r1 = thresholds['range1']
    r2 = thresholds['range2']
    com = thresholds['common']
    
    code = f"""
# 红色阈值配置（自动生成）
lower_red1 = np.array([{r1['H Min']}, {com['S Min']}, {com['V Min']}])
upper_red1 = np.array([{r1['H Max']}, {com['S Max']}, {com['V Max']}])
lower_red2 = np.array([{r2['H Min']}, {com['S Min']}, {com['V Min']}])
upper_red2 = np.array([{r2['H Max']}, {com['S Max']}, {com['V Max']}])

# 创建掩码
mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask = cv2.bitwise_or(mask1, mask2)
"""
    
    code_file = os.path.join(config_dir, "threshold_code.py")
    with open(code_file, 'w') as f:
        f.write(code)
    
    print(f"代码片段已保存到: {code_file}")

def load_thresholds():
    """加载阈值配置"""
    config_file = os.path.join(config_dir, "red_thresholds_v2.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                thresholds = json.load(f)
            
            # 设置区间1
            cv2.setTrackbarPos('H1 Min', window_name, thresholds['range1']['H Min'])
            cv2.setTrackbarPos('H1 Max', window_name, thresholds['range1']['H Max'])
            
            # 设置区间2
            cv2.setTrackbarPos('H2 Min', window_name, thresholds['range2']['H Min'])
            cv2.setTrackbarPos('H2 Max', window_name, thresholds['range2']['H Max'])
            
            # 设置共用参数
            cv2.setTrackbarPos('S Min', window_name, thresholds['common']['S Min'])
            cv2.setTrackbarPos('V Min', window_name, thresholds['common']['V Min'])
            cv2.setTrackbarPos('S Max', window_name, thresholds['common']['S Max'])
            cv2.setTrackbarPos('V Max', window_name, thresholds['common']['V Max'])
            
            print("已加载保存的阈值配置")
            return True
        else:
            print("无保存的配置，使用默认值")
            return False
    except Exception as e:
        print(f"加载配置失败: {e}")
        return False

def print_thresholds():
    """打印当前阈值"""
    h1_min = cv2.getTrackbarPos('H1 Min', window_name)
    h1_max = cv2.getTrackbarPos('H1 Max', window_name)
    h2_min = cv2.getTrackbarPos('H2 Min', window_name)
    h2_max = cv2.getTrackbarPos('H2 Max', window_name)
    s_min = cv2.getTrackbarPos('S Min', window_name)
    v_min = cv2.getTrackbarPos('V Min', window_name)
    s_max = cv2.getTrackbarPos('S Max', window_name)
    v_max = cv2.getTrackbarPos('V Max', window_name)
    
    print("\n当前红色阈值:")
    print(f"区间1 (低值红): H=[{h1_min}-{h1_max}]")
    print(f"区间2 (高值红): H=[{h2_min}-{h2_max}]")
    print(f"共用: S=[{s_min}-{s_max}], V=[{v_min}-{v_max}]")
    
    # 显示HSV范围
    print(f"\n对应的HSV范围:")
    print(f"lower_red1 = np.array([{h1_min}, {s_min}, {v_min}])")
    print(f"upper_red1 = np.array([{h1_max}, {s_max}, {v_max}])")
    print(f"lower_red2 = np.array([{h2_min}, {s_min}, {v_min}])")
    print(f"upper_red2 = np.array([{h2_max}, {s_max}, {v_max}])")

# 加载保存的配置
load_thresholds()

print("\n使用说明:")
print("1. 调整 H1 Min/H1 Max: 控制低值红色范围 (通常0-10)")
print("2. 调整 H2 Min/H2 Max: 控制高值红色范围 (通常170-180)")
print("3. 调整 S Min/V Min: 提高值可减少环境光干扰")
print("4. 按 's' 保存配置")
print("5. 按 'p' 打印当前阈值")
print("6. 按 'q' 退出")

# 用于显示检测效果的变量
last_radius = 0

while True:
    ret, frame = cap.read()
    if not ret:
        continue
    
    frame_copy = frame.copy()
    
    # 获取当前阈值
    h1_min = cv2.getTrackbarPos('H1 Min', window_name)
    h1_max = cv2.getTrackbarPos('H1 Max', window_name)
    h2_min = cv2.getTrackbarPos('H2 Min', window_name)
    h2_max = cv2.getTrackbarPos('H2 Max', window_name)
    s_min = cv2.getTrackbarPos('S Min', window_name)
    v_min = cv2.getTrackbarPos('V Min', window_name)
    s_max = cv2.getTrackbarPos('S Max', window_name)
    v_max = cv2.getTrackbarPos('V Max', window_name)
    
    # HSV颜色空间转换
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 创建两个红色范围的掩码
    lower_red1 = np.array([h1_min, s_min, v_min])
    upper_red1 = np.array([h1_max, s_max, v_max])
    lower_red2 = np.array([h2_min, s_min, v_min])
    upper_red2 = np.array([h2_max, s_max, v_max])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # 形态学去噪
    kernel = np.ones((5, 5), np.uint8)
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)
    
    # 查找轮廓并检测圆
    contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # 找到最大轮廓
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 计算最小外接圆
        ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)
        
        if radius > 5:  # 忽略太小的检测
            # 绘制圆
            cv2.circle(frame_copy, (int(x), int(y)), int(radius), (0, 255, 0), 2)
            cv2.circle(frame_copy, (int(x), int(y)), 5, (0, 0, 255), -1)
            
            # 显示半径
            cv2.putText(frame_copy, f"Radius: {radius:.1f} px", 
                       (int(x)+20, int(y)), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, (0, 255, 0), 2)
            
            last_radius = radius
            
            # 计算距离（假设焦距727.8）
            if radius > 0:
                distance_cm = (4.0 * 727.8) / (radius * 2)
                cv2.putText(frame_copy, f"Dist: {distance_cm:.0f} cm", 
                           (int(x)+20, int(y)+30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (255, 255, 0), 2)
    
    # 在左上角显示当前阈值
    cv2.putText(frame_copy, f"H1: [{h1_min}-{h1_max}]", 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame_copy, f"H2: [{h2_min}-{h2_max}]", 
               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame_copy, f"S: [{s_min}-{s_max}]", 
               (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame_copy, f"V: [{v_min}-{v_max}]", 
               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    if last_radius > 0:
        cv2.putText(frame_copy, f"Detected R: {last_radius:.1f} px", 
                   (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 创建显示面板
    # 第一行：原图和掩码
    h1 = cv2.hconcat([frame, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])
    # 第二行：结果和检测
    h2 = cv2.hconcat([cv2.cvtColor(mask_clean, cv2.COLOR_GRAY2BGR), frame_copy])
    # 合并
    display = cv2.vconcat([h1, h2])
    
    # 调整显示大小
    display_resized = cv2.resize(display, (800, 600))
    cv2.imshow(window_name, display_resized)
    
    # 按键处理
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        save_thresholds()
    elif key == ord('p'):
        print_thresholds()
    elif key == ord('r'):  # 重置半径显示
        last_radius = 0

# 清理
cap.release()
cv2.destroyAllWindows()
print("程序结束")