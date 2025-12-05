#测量安全区面积范围
import cv2
import numpy as np
import json

def load_color(color_name):
    with open(f'config/hsv_thresholds_{color_name}.json', 'r') as f:
        config = json.load(f)
        lower = [config["H Min"], config["S Min"], config["V Min"]]
        upper = [config["H Max"], config["S Max"], config["V Max"]]
        return {"lower": lower, "upper": upper}

def measure_safe_zone_area():
    cap = cv2.VideoCapture(0)  # 摄像头ID
    
    print("======= 安全区面积测量 =======")
    print("操作说明:")
    print("1. 将摄像头对准安全区（距离和角度与实际比赛一致）")
    print("2. 确保能清晰看到紫色围栏")
    print("3. 按空格键测量面积")
    print("4. 按q键退出")
    print("=============================")
    
    measured_areas = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 紫色检测
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        purple_config = load_color("purple")
        lower = np.array(purple_config["lower"])
        upper = np.array(purple_config["upper"])
        mask = cv2.inRange(hsv, lower, upper)
        
        # 形态学操作（与vision.py一致）
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 显示结果
        display = frame.copy()
        
        if contours:
            # 找到最大轮廓（应该是安全区）
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # 绘制轮廓和面积
            cv2.drawContours(display, [largest_contour], -1, (255, 0, 255), 3)
            
            # 显示面积
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(display, f"面积: {int(area)}", (cx-100, cy),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
            
            # 显示轮廓数量
            cv2.putText(display, f"轮廓数: {len(contours)}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # 显示图像
        cv2.imshow('原图', display)
        cv2.imshow('紫色掩码', mask)
        
        # 按键处理
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):  # 空格键记录
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                measured_areas.append(area)
                print(f"测量 {len(measured_areas)}: 面积 = {int(area)} 像素")
                
                # 实时分析
                if len(measured_areas) >= 2:
                    avg_area = np.mean(measured_areas)
                    min_area = np.min(measured_areas)
                    max_area = np.max(measured_areas)
                    print(f"  平均值: {int(avg_area)}, 范围: [{int(min_area)}, {int(max_area)}]")
        
        # 连续测量模式（可选）
        elif key == ord('c'):
            print("进入连续测量模式...")
            for i in range(10):  # 连续测10次
                ret, frame = cap.read()
                if not ret:
                    break
                
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, lower, upper)
                kernel = np.ones((5, 5), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest_contour)
                    measured_areas.append(area)
                    print(f"连续测量 {i+1}: {int(area)}")
                
                time.sleep(0.1)
            
            print(f"连续测量完成，共 {len(measured_areas)} 次")
    
    cap.release()
    cv2.destroyAllWindows()
    
    # 输出最终结果
    if measured_areas:
        print("\n======= 测量结果分析 =======")
        print(f"总测量次数: {len(measured_areas)}")
        print(f"最小面积: {int(np.min(measured_areas))}")
        print(f"最大面积: {int(np.max(measured_areas))}")
        print(f"平均面积: {int(np.mean(measured_areas))}")
        print(f"中位数: {int(np.median(measured_areas))}")
        print(f"标准差: {int(np.std(measured_areas))}")
        
        # 推荐阈值（保守估计）
        recommended_min = int(np.min(measured_areas) * 0.5)  # 留50%余量
        print(f"\n推荐最小面积阈值: {recommended_min}")
        print(f"(当前vision.py中使用的是: if area > 500:)")
        
        # 检查其他轮廓的面积（排除干扰）
        print("\n【重要】请检查是否有其他紫色干扰物:")
        print("如果其他紫色物体面积小于推荐阈值，就不会被误判为安全区")
    
    return measured_areas

if __name__ == "__main__":
    import time
    measured_areas = measure_safe_zone_area()