import subprocess, cv2
import json
import numpy as np
import os

cam = cv2.VideoCapture(0)

NUM_LEDS = 5
coords = []

# Create a folder if it doesn't exist
save_dir = "led_images"
os.makedirs(save_dir, exist_ok=True)



if not cam.isOpened():
    print("Cannot open camera")
    exit()

for i in range(20):  
    ret, frame = cam.read()


for i in range(NUM_LEDS):

    subprocess.run(["ssh", "martin@ledpi.local", f"python3 set_led.py {i}"])

    ret, frame = cam.read()

    gray = np.copy(frame)
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, ksize=(11,11), sigmaX=3, sigmaY=3)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray) # cv2.minMaxLoc returns (minVal, maxVal, minLoc, maxLoc)

    coords.append((maxLoc[0], maxLoc[1]))

    circle = np.copy(frame)
    circle = cv2.circle(circle, maxLoc, 10, (0,0,255), 5)


    if ret:
        cv2.imshow('Camera Feed', circle)
        cv2.imwrite(os.path.join(save_dir, f'led_{i}.png'), circle)
    cv2.waitKey(1)

cam.release()