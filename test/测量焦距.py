import cv2
import numpy as np
import json
from datetime import datetime

class SmartCalibrator:
    def __init__(self):
        self.known_distance = 100.0  # 厘米
        self.known_diameter = 4.0    # 厘米
        self.calibration_results = []
        
    def detect_and_measure_ball(self, frame):
        """检测并测量球"""
        # 转换为HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 检测橙色/红色（乒乓球颜色）
        # 橙色范围
        lower_orange = np.array([5, 100, 100])
        upper_orange = np.array([15, 255, 255])
        
        # 红色范围
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        # 创建掩码
        mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask_orange, cv2.bitwise_or(mask_red1, mask_red2))
        
        # 形态学处理
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, None, frame
        
        # 找到最大轮廓
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 计算最小外接圆
        (x, y), radius = cv2.minEnclosingCircle(largest_contour)
        
        # 在图像上标记
        result_frame = frame.copy()
        cv2.circle(result_frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
        cv2.circle(result_frame, (int(x), int(y)), 5, (0, 0, 255), -1)
        
        # 显示直径
        cv2.putText(result_frame, f"Diameter: {radius*2:.1f}px", 
                   (int(x)-60, int(y)-30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (0, 255, 255), 2)
        
        return radius * 2, radius, result_frame
    
    def calibrate_with_live_video(self):
        """使用实时视频进行标定"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("实时标定模式")
        print("请将乒乓球放在100厘米处")
        print("按 's' 开始测量，按 'q' 退出")
        
        measurements = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 检测球
            diameter, radius, detected_frame = self.detect_and_measure_ball(frame)
            
            # 显示
            cv2.imshow('Calibration Live', detected_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('s') and diameter:  # 开始测量
                print(f"\n测量 {len(measurements)+1}:")
                print(f"  检测直径: {diameter:.1f} 像素")
                print(f"  检测半径: {radius:.1f} 像素")
                
                # 计算焦距
                focal_length = (diameter * self.known_distance) / self.known_diameter
                print(f"  计算焦距: {focal_length:.1f} 像素")
                
                measurements.append({
                    'diameter': float(diameter),
                    'radius': float(radius),
                    'focal_length': float(focal_length),
                    'timestamp': datetime.now().isoformat()
                })
                
                # 保存当前帧
                cv2.imwrite(f'measurement_{len(measurements)}.jpg', detected_frame)
                
                if len(measurements) >= 5:
                    print("\n已完成5次测量")
                    break
            
            elif key == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if measurements:
            return self._calculate_final_result(measurements)
        
        return None
    
    def _calculate_final_result(self, measurements):
        """计算最终结果"""
        # 计算平均值
        diameters = [m['diameter'] for m in measurements]
        focal_lengths = [m['focal_length'] for m in measurements]
        
        avg_diameter = np.mean(diameters)
        avg_focal = np.mean(focal_lengths)
        std_focal = np.std(focal_lengths)
        
        # 计算FOV
        frame_width = 640
        fov = 2 * np.degrees(np.arctan(frame_width / (2 * avg_focal)))
        
        # 保存结果
        result = {
            'focal_length': float(avg_focal),
            'focal_length_std': float(std_focal),
            'fov_horizontal': float(fov),
            'avg_diameter_px': float(avg_diameter),
            'measurements': measurements,
            'known_distance_cm': self.known_distance,
            'known_diameter_cm': self.known_diameter,
            'calibration_time': datetime.now().isoformat()
        }
        
        with open('smart_calibration.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print("\n" + "="*50)
        print("标定完成!")
        print(f"平均检测直径: {avg_diameter:.1f} 像素")
        print(f"推荐焦距: {avg_focal:.1f} ± {std_focal:.1f} 像素")
        print(f"水平FOV: {fov:.2f} 度")
        print(f"详细结果已保存到: smart_calibration.json")
        
        return avg_focal, fov

