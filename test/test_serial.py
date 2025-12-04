import serial
ser = serial.Serial('/dev/ttyS3', 115200, timeout=1)
ser.write(b"TEST\n")
data = ser.read(100)
print(f"收到: {data}")
ser.close()