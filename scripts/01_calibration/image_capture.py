import subprocess, cv2
import time
import os

cam = cv2.VideoCapture(0)

# angles = [0, 45, 90, 135, 180, 225, 270, 315]

if not cam.isOpened():
    print("Cannot open camera")
    exit()

total_leds = 200

# file locations on RPi
PYTHON_PATH = "/home/martin/led-env/bin/python3"
LED_SCRIPT = "/home/martin/led_project/set_led.py"
CLEAR_SCRIPT = "/home/martin/led_project/clear.py"
CAPTURE_DIR = "led_images"

os.makedirs(CAPTURE_DIR, exist_ok=True)

# warm up camera
for i in range(20):
    ret, frame = cam.read()

angle = input("scan angle: ")

for i in range(total_leds):
    # turn on LED i via remote script
    subprocess.run(["ssh", "martin@ledpi.local", f"sudo {PYTHON_PATH} {LED_SCRIPT} {i}"])
    ret, frame = cam.read()

    if not ret:
        print(f"Camera read failed for LED {i}")
        break

    cv2.imwrite(os.path.join(CAPTURE_DIR, f'led_{i}_angle_{angle}.png'), frame)
    subprocess.run(["ssh", "martin@ledpi.local", f"sudo {PYTHON_PATH} {CLEAR_SCRIPT}"])

    time.sleep(0.1)

cam.release()