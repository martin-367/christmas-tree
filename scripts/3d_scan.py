import subprocess, cv2
import os
import json
import math
import numpy as np

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Cannot open camera")
    exit()

NUM_LEDS = 50
coords_by_scan = []  # list of lists: for each scan, list of (x

# file locations on RPi
PYTHON_PATH = "/home/martin/led-env/bin/python3"
LED_SCRIPT = "/home/martin/led_project/set_led.py"

# Create a folder if it doesn't exist
capture_dir = "led_images"
save_dir = "coordinates"
os.makedirs(capture_dir, exist_ok=True)
os.makedirs(save_dir, exist_ok=True)

# warm up camera
for i in range(20):
    ret, frame = cam.read()

def detect_led_in_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, ksize=(11,11), sigmaX=3, sigmaY=3)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray)
    return (int(maxLoc[0]), int(maxLoc[1])), maxVal

angles = [0, 90, 180, 270]  # predefined angles for scanning

for scan_idx, angle in enumerate(angles):
    for i in range(NUM_LEDS):
        subprocess.run(["ssh", "martin@ledpi.local", f"sudo {PYTHON_PATH} {LED_SCRIPT} {i}"])
        ret, frame = cam.read()

        scan_coords = []

        if not ret:
            print(f"Camera read failed for LED {i} on scan {scan_idx}")
            scan_coords.append(None)
            continue

        (x, y), strength = detect_led_in_frame(frame)
        coords_by_scan.append((x, y))
        circle = frame.copy()
        circle = cv2.circle(circle, (x, y), 10, (0,0,255), 5)
        cv2.imshow('Camera Feed', circle)
        cv2.imwrite(os.path.join(capture_dir, f'led_{i}_scan_{scan_idx}.png'), circle)
        cv2.waitKey(1)

    coords_by_scan.append(scan_coords)

cam.release()
cv2.destroyAllWindows()



LED_positions_3D = []

for led_idx in range(NUM_LEDS):
    LED_positions = []
    for scan_idx, angle in enumerate(angles):
        position = coords_by_scan[scan_idx][led_idx]
        LED_positions.append(position)
    
    # LED_positions are [(x,z) (y,z) (-x,z) (-y,z)] for this LED
    xcoord = np.average([LED_positions[0][0], -LED_positions[2][0]])
    ycoord = np.average([LED_positions[1][0], -LED_positions[3][0]])
    zccoord = np.average([pos[1] for pos in LED_positions])
    print(f"LED {led_idx}: 3D position = ({xcoord}, {ycoord}, {zccoord})")

    LED_positions_3D.append((xcoord, ycoord, zccoord))

print(LED_positions_3D)

save_file = open((os.path.join(save_dir, "savedata.json")), "w")
json.dump(LED_positions_3D, save_file, indent=6)
save_file.close()