# 面积过滤范围测试
import cv2
import numpy as np
import json
import time

def load_color(color_name):
    with open(f'config/hsv_thresholds_{color_name}.json', 'r') as f:
        config = json.load(f)
        lower = [config["H Min"], config["S Min"], config["V Min"]]
        upper = [config["H Max"], config["S Max"], config["V Max"]]
        return {"lower": lower, "upper": upper}

def main():
    cap = cv2.VideoCapture(0)  # 摄像头ID
    
    # 创建滑动条调整面积范围
    cv2.namedWindow('调试')
    cv2.createTrackbar('最小面积', '调试', 100, 5000, lambda x: None)
    cv2.createTrackbar('最大面积', '调试', 1000, 5000, lambda x: None)
    
    print("按空格键保存当前帧，按q键退出")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 复制一份用于显示
        display = frame.copy()
        
        # 获取滑动条值
        min_area = cv2.getTrackbarPos('最小面积', '调试')
        max_area = cv2.getTrackbarPos('最大面积', '调试')
        
        # 颜色检测
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        color_config = load_color("red")  # 测试红色
        lower = np.array(color_config["lower"])
        upper = np.array(color_config["upper"])
        mask = cv2.inRange(hsv, lower, upper)
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 绘制所有轮廓并显示面积
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            
            # 绘制轮廓
            color = (0, 255, 0) if min_area <= area <= max_area else (0, 0, 255)
            cv2.drawContours(display, [cnt], -1, color, 2)
            
            # 显示面积
            (x, y), _ = cv2.minEnclosingCircle(cnt)
            cv2.putText(display, f"{int(area)}", (int(x), int(y)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # 在控制台输出
            if area > 50:  # 只显示显著轮廓
                status = "✅ 在范围内" if min_area <= area <= max_area else "❌ 超出范围"
                print(f"轮廓{i+1}: 面积={int(area)} {status}")
        
        # 显示参数
        cv2.putText(display, f"面积范围: [{min_area}, {max_area}]", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # 显示图像
        cv2.imshow('调试', display)
        cv2.imshow('掩码', mask)
        
        # 按键处理
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):  # 空格键保存当前参数
            print(f"\n推荐面积范围: {min_area} - {max_area}")
            print("可以将这些值填入代码中")
        
        time.sleep(0.1)  # 控制刷新频率
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()