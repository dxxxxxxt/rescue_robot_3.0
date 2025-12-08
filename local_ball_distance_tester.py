import cv2
import sys
import os

# 添加src目录到Python路径，以便导入vision模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import vision


def main():
    # 配置参数
    camera_id = 0  # 摄像头ID
    target_color = "black"  # 目标颜色（red/blue/yellow/black）
    frame_width = 640
    frame_height = 480
    flip_image = True  # 是否翻转图像（解决画面倒置问题）
    flip_mode = 0  # 翻转模式：0=垂直翻转（上下颠倒）, 1=水平翻转（左右颠倒）, -1=垂直和水平翻转
    
    # 初始化摄像头
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"摄像头 {camera_id} 打开失败")
        return
    
    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
    print(f"开始检测{target_color}色小球")
    print("按 'q' 退出")
    
    try:
        while True:
            # 读取摄像头图像
            ret, frame = cap.read()
            if not ret:
                print("读取帧失败")
                break
            
            # 翻转图像（解决画面倒置问题）
            if flip_image:
                frame = cv2.flip(frame, flip_mode)
            
            # 检测小球
            balls = vision.find_balls(frame, target_color)
            
            if balls:
                # 取最大的小球
                x, y, radius = max(balls, key=lambda b: b[2])
                
                # 计算偏移量
                dx, dy = vision.calculate_offset(x, y, frame_width, frame_height)
                
                # 计算距离
                raw_distance = vision.calculate_distance(radius)
                distance = vision.smooth_distance(raw_distance)
                
                # 在图像上显示信息
                cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
                cv2.putText(frame, f"dis: {distance} cm", (x - 50, y - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"dd: dx={dx}, dy={dy}", (x - 70, y + 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # 在终端打印信息
                print(f"小球坐标: ({x}, {y}), 半径: {radius} 像素")
                print(f"偏移量: dx={dx}, dy={dy}")
                print(f"距离: {distance} cm")
                print("=" * 50)
            else:
                # 没有检测到小球
                cv2.putText(frame, "no see", (50, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                print("未检测到小球")
                print("=" * 50)
            
            # 显示图像
            cv2.imshow("小球距离测量", frame)
            
            # 按 'q' 退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("用户中断")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("程序结束")


if __name__ == "__main__":
    main()