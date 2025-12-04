import serial
import time
# 红色小球=1
# 蓝色小球=2
# 黄色小球=3
# 黑色小球=4
# 红色安全区=5
# 蓝色安全区=6

ser = serial.Serial('/dev/ttyS3', 115200)
print("串口已初始化并打开")
def read_ecu_command():
    """读取电控发送的数组信号"""
    try:
        # 检查串口是否初始化成功且处于打开状态
        if  not ser or not  ser.is_open:
            print("警告: 串口未初始化或已关闭，无法接收数据")
            return None
        
        if ser.in_waiting > 0:
            cmd = ser.read(ser.in_waiting).decode('utf-8').strip()
            print(f"收到电控信号: {list(cmd)}")
            return list(cmd)  # 返回数组格式
        return None
    except Exception as e:
        print(f"接收数据出错: {e}")
        return None

def send_data(dx, dy, distance, ball_id):
    """
    发送 ASCII 字符串给 STM32
    格式: "dx:100 dy:200 dis:200 id:1"
    """
    # 构造严格匹配 scanf 的字符串
    msg = f"dx:{dx} dy:{dy} dis:{distance} id:{ball_id}\n"
    
    # 发送 ASCII 字节
    ser.write(msg.encode('ascii'))
    print(f"发送: '{msg}'")

def send_no_target():
    """没有看到目标时发送0"""
    msg = "dx:0 dy:0 dis:0 id:0"
    ser.write(msg.encode('ascii'))
    print(f"发送: '{msg}' (无目标)")

def close_serial():
    """关闭串口"""
    if ser and ser.is_open:
        ser.close()
        print("串口已关闭")

#-----------------------------------------------------------------------------------------------
# 测试1
# if ser and ser.is_open:
#     print("串口已初始化并打开")
#     while True:
#         cmd=ser.read().decode('utf-8')
#         print(f"收到电控数据: {cmd}")
#         send_data(100, 200, 200, 2) 

# 测试2
# try:
#     while True:
#         cmd=ser.read().decode('utf-8')
#         print(f"收到电控数据: {cmd}")

# except KeyboardInterrupt:
#     print("\n程序被中断")
# finally:
#     if ser.is_open:
#         ser.close()
#         print("串口已关闭")