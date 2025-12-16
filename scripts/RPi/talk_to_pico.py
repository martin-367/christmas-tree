import serial
import time

# /dev/serial0 is the default alias for the primary UART pins
ser = serial.Serial('/dev/serial0', 115200, timeout=1)
ser.reset_input_buffer()

print("Connecting to Pico...")

try:
    while True:
        # 1. Send data to Pico
        message = "Ping\n"
        ser.write(message.encode('utf-8'))
        print(f"Sent: {message.strip()}")

        # 2. Wait for a response
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(f"Pico said: {line}")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting Program")
    ser.close()