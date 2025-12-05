import cv2
import numpy as np
import json

def load_color(color_name):
    """加载颜色配置"""
    try:
        with open(f'config/hsv_thresholds_{color_name}.json', 'r') as f:
            config = json.load(f)
            lower = [config["H Min"], config["S Min"], config["V Min"]]
            upper = [config["H Max"], config["S Max"], config["V Max"]]
            return {"lower": lower, "upper": upper}
    except:
        return {"lower": [0,0,0], "upper": [180,255,255]}

def test_circularity_threshold():
    """测试不同圆形度阈值的效果"""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # 初始圆形度阈值
    circularity_threshold = 0.6
    print("按 '+' 增加阈值，按 '-' 减小阈值，按 'q' 退出")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        color_config = load_color("red")  # 测试红色小球
        lower = np.array(color_config["lower"])
        upper = np.array(color_config["upper"])
        mask = cv2.inRange(hsv, lower, upper)
        
        # 形态学操作
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        balls = []
        all_shapes = []  # 所有检测到的形状
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 50 < area < 2000:  # 面积过滤
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    # 记录所有形状信息
                    all_shapes.append({
                        'contour': cnt,
                        'area': area,
                        'perimeter': perimeter,
                        'circularity': circularity,
                        'is_ball': circularity > circularity_threshold
                    })
                    
                    if circularity > circularity_threshold:
                        (x, y), radius = cv2.minEnclosingCircle(cnt)
                        balls.append((int(x), int(y), int(radius)))
        
        # 显示结果
        display = frame.copy()
        
        # 绘制所有检测到的形状
        for shape in all_shapes:
            color = (0, 255, 0) if shape['is_ball'] else (0, 0, 255)  # 绿色=球，红色=非球
            cv2.drawContours(display, [shape['contour']], -1, color, 2)
            
            # 显示圆形度值
            M = cv2.moments(shape['contour'])
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                text = f"{shape['circularity']:.2f}"
                cv2.putText(display, text, (cx-20, cy), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 显示当前阈值
        cv2.putText(display, f"阈值: {circularity_threshold:.2f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(display, f"检测到球数: {len(balls)}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # 显示统计信息
        if all_shapes:
            avg_circ = np.mean([s['circularity'] for s in all_shapes])
            cv2.putText(display, f"平均圆形度: {avg_circ:.2f}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
        cv2.imshow('圆形度阈值测试', display)
        
        # 键盘控制
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('+') or key == ord('='):
            circularity_threshold += 0.05
            print(f"阈值增加到: {circularity_threshold:.2f}")
        elif key == ord('-') or key == ord('_'):
            circularity_threshold -= 0.05
            print(f"阈值减少到: {circularity_threshold:.2f}")
        elif key == ord('s'):
            # 保存当前阈值
            print(f"当前阈值 {circularity_threshold:.2f} 已保存")
            with open('circularity_threshold.txt', 'w') as f:
                f.write(str(circularity_threshold))
    
    cap.release()
    cv2.destroyAllWindows()
    return circularity_threshold

if __name__ == "__main__":
    final_threshold = test_circularity_threshold()
    print(f"\n建议圆形度阈值: {final_threshold:.2f}")