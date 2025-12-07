import cv2
import numpy as np
import json

class DistanceTester:
    def __init__(self, camera_id=0, color_name="red", focal_length=727.8, ball_real_diameter=4.0):
        """
        初始化距离测量器
        参数:
            camera_id: 摄像头ID
            color_name: 要检测的目标颜色
            focal_length: 标定的焦距(像素)
            ball_real_diameter: 目标真实直径(厘米)
        """
        self.camera_id = camera_id
        self.color_name = color_name
        self.focal_length = focal_length
        self.ball_real_diameter = ball_real_diameter
        self.cap = None
        
        # 加载颜色配置
        self.color_config = self.load_color(color_name)
        
        # 距离历史记录，用于平滑滤波
        self.distance_history = []
        self.window_size = 5
    
    def load_color(self, color_name):
        """加载HSV颜色阈值配置"""
        try:
            with open(f'config/hsv_thresholds_{color_name}.json', 'r') as f:
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
                    return {"range1": range1, "range2": range2, "is_double_range": True}
                else:
                    # 单区间结构（适用于大多数颜色）
                    lower = [config["H Min"], config["S Min"], config["V Min"]]
                    upper = [config["H Max"], config["S Max"], config["V Max"]]
                    return {"lower": lower, "upper": upper, "is_double_range": False}
        except Exception as e:
            print(f"找不到 {color_name} 的配置文件: {e}")
            # 返回默认的红色配置（双区间）
            return {
                "range1": {"lower": [0, 100, 100], "upper": [10, 255, 255]},
                "range2": {"lower": [169, 100, 100], "upper": [180, 255, 255]},
                "is_double_range": True
            }
    
    def calculate_distance(self, ball_radius):
        """计算距离"""
        if ball_radius <= 0:
            return 100
        
        pixel_diameter = ball_radius * 2
        distance = (self.ball_real_diameter * self.focal_length) / pixel_diameter
        return int(distance)
    
    def smooth_distance(self, distance):
        """平滑距离值"""
        self.distance_history.append(distance)
        if len(self.distance_history) > self.window_size:
            self.distance_history.pop(0)
        
        return int(np.mean(self.distance_history))
    
    def detect_object(self, frame):
        """检测目标物体"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 根据配置类型创建掩码
        if self.color_config["is_double_range"]:
            # 双区间处理（如红色）
            lower1 = np.array(self.color_config["range1"]["lower"])
            upper1 = np.array(self.color_config["range1"]["upper"])
            mask1 = cv2.inRange(hsv, lower1, upper1)
            
            lower2 = np.array(self.color_config["range2"]["lower"])
            upper2 = np.array(self.color_config["range2"]["upper"])
            mask2 = cv2.inRange(hsv, lower2, upper2)
            
            # 合并两个区间的掩码
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            # 单区间处理
            lower = np.array(self.color_config["lower"])
            upper = np.array(self.color_config["upper"])
            mask = cv2.inRange(hsv, lower, upper)
        
        # 形态学操作
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area > 50:
                (x, y), radius = cv2.minEnclosingCircle(largest_contour)
                
                # 圆形度检查
                perimeter = cv2.arcLength(largest_contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.7:
                        return int(x), int(y), int(radius)
        
        return None, None, None
    
    def start(self):
        """开始测量"""
        # 初始化摄像头
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"摄像头 {self.camera_id} 打开失败")
            return False
        
        # 设置摄像头参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print(f"开始测量距离，目标颜色: {self.color_name}")
        print("按 'q' 退出")
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("读取帧失败")
                    break
                
                # 检测目标
                x, y, radius = self.detect_object(frame)
                
                if x is not None and y is not None and radius > 0:
                    # 计算距离
                    raw_distance = self.calculate_distance(radius)
                    distance = self.smooth_distance(raw_distance)
                    
                    # 在图像上显示信息
                    cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
                    cv2.putText(frame, f"距离: {distance} cm", (x - 50, y - 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # 打印距离
                    print(f"检测到目标，距离: {distance} cm")
                else:
                    # 没有检测到目标
                    cv2.putText(frame, "未检测到目标", (50, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    print("未检测到目标")
                
                # 显示图像
                cv2.imshow("距离测量器", frame)
                
                # 按 q 退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("用户中断")
        
        finally:
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()
            print("程序结束")
        
        return True

if __name__ == "__main__":
    # 配置参数
    CAMERA_ID = 0  # 摄像头ID，通常笔记本内置摄像头为0
    TARGET_COLOR = "red"  # 要检测的颜色 (red/blue/yellow/black)
    FOCAL_LENGTH = 727.8  # 标定的焦距(像素)
    BALL_REAL_DIAMETER = 4.0  # 小球真实直径(厘米)
    
    # 创建并运行距离测量器
    tester = DistanceTester(
        camera_id=CAMERA_ID,
        color_name=TARGET_COLOR,
        focal_length=FOCAL_LENGTH,
        ball_real_diameter=BALL_REAL_DIAMETER
    )
    tester.start()
