import subprocess, cv2
import json
import numpy as np
import os
import math

cam = cv2.VideoCapture(0)

NUM_LEDS = 50
coords_by_scan = []  # list of lists: for each scan, list of (x,y) per LED

# Create a folder if it doesn't exist
capture_dir = "led_images"
save_dir = "coordinates"
os.makedirs(capture_dir, exist_ok=True)
os.makedirs(save_dir, exist_ok=True)

PYTHON_PATH = "/home/martin/led-env/bin/python3"
LED_SCRIPT = "/home/martin/led_project/set_led.py"

if not cam.isOpened():
    print("Cannot open camera")
    exit()

# warm up camera
for i in range(20):
    ret, frame = cam.read()

# Ask user for scan angles (manual rotation)
angles_input = input("Enter comma-separated scan angles in degrees (e.g. 0,30,60): ").strip()
angles = [float(a.strip()) for a in angles_input.split(",") if a.strip()!='']
if len(angles) < 2:
    print("Need at least two scan angles to triangulate 3D coordinates.")
    cam.release()
    cv2.destroyAllWindows()
    exit()

print(f"Will perform {len(angles)} scans at angles: {angles}")
print("For each angle the script will iterate all LEDs. Rotate the rig to the first angle now and press Enter.")
input("Press Enter to start the first scan...")

# detect LED location in current frame
def detect_led_in_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, ksize=(11,11), sigmaX=3, sigmaY=3)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray)
    return (int(maxLoc[0]), int(maxLoc[1])), maxVal

# Acquire scans
for scan_idx, angle in enumerate(angles):
    print(f"Starting scan {scan_idx+1}/{len(angles)} at angle {angle} degrees.")
    scan_coords = []
    # ensure user had rotated rig to this angle
    if scan_idx > 0:
        input(f"Rotate rig to angle {angle} and press Enter to continue...")

    for i in range(NUM_LEDS):
        # turn on LED i via remote script
        subprocess.run(["ssh", "martin@ledpi.local", f"sudo {PYTHON_PATH} {LED_SCRIPT} {i}"])
        # allow LED to settle and camera to capture
        ret, frame = cam.read()
        if not ret:
            print(f"Camera read failed for LED {i} on scan {scan_idx}")
            scan_coords.append(None)
            continue

        (x, y), strength = detect_led_in_frame(frame)
        scan_coords.append((x, y))

        circle = frame.copy()
        circle = cv2.circle(circle, (x, y), 10, (0,0,255), 5)

        cv2.imshow('Camera Feed', circle)
        cv2.imwrite(os.path.join(capture_dir, f'led_{i}_scan_{scan_idx}.png'), circle)
        cv2.waitKey(1)

    coords_by_scan.append(scan_coords)
    print(f"Completed scan {scan_idx+1}/{len(angles)}")

cam.release()
cv2.destroyAllWindows()

# Save raw 2D detections
raw_save = {
    "angles": angles,
    "num_leds": NUM_LEDS,
    "detections": coords_by_scan
}
with open(os.path.join(save_dir, "savedata_2d.json"), "w") as f:
    json.dump(raw_save, f, indent=2)

# Triangulate 3D positions
# Ask for camera intrinsics or use defaults
img_sample = cv2.imread(os.path.join(capture_dir, f'led_0_scan_0.png'))
if img_sample is None:
    # try reading any saved image to get size
    for fname in os.listdir(capture_dir):
        if fname.endswith(".png"):
            img_sample = cv2.imread(os.path.join(capture_dir, fname))
            break

if img_sample is None:
    print("No sample images found to infer image size. Skipping 3D triangulation.")
    with open(os.path.join(save_dir, "savedata.json"), "w") as f:
        json.dump(coords_by_scan, f, indent=2)
    exit()

h, w = img_sample.shape[:2]
print(f"Detected image size: width={w}, height={h}")

use_custom_intr = input("Provide camera intrinsics? (y/N) ").strip().lower()
if use_custom_intr == 'y':
    fx = float(input("fx (pixels): ").strip())
    fy = float(input("fy (pixels): ").strip())
    cx = float(input("cx (pixels): ").strip())
    cy = float(input("cy (pixels): ").strip())
else:
    # reasonable default: focal length ~ image width in pixels
    fx = fy = w
    cx = w/2.0
    cy = h/2.0
    print(f"Using default intrinsics fx=fy={fx}, cx={cx}, cy={cy}")

K = np.array([[fx, 0, cx],
              [0, fy, cy],
              [0,  0,  1]], dtype=float)
K_inv = np.linalg.inv(K)

# rotation matrix about Y axis (degrees -> radians)
def R_y(deg):
    th = math.radians(deg)
    c = math.cos(th)
    s = math.sin(th)
    return np.array([[ c, 0,  s],
                     [ 0, 1,  0],
                     [-s, 0,  c]], dtype=float)

# For each LED, build A matrix stacking (I - v v^T) R_k rows and find p0 as smallest singular vector
three_d_coords = []
for led_idx in range(NUM_LEDS):
    # collect valid detections across scans
    vs = []      # normalized ray directions
    Rmats = []   # rotation matrices for each scan
    valid = True
    for scan_idx, angle in enumerate(angles):
        det = coords_by_scan[scan_idx][led_idx]
        if det is None:
            valid = False
            break
        u, v = det
        pix = np.array([u, v, 1.0], dtype=float)
        ray = K_inv @ pix
        ray = ray / np.linalg.norm(ray)
        vs.append(ray)
        Rmats.append(R_y(angle))
    if not valid or len(vs) < 2:
        three_d_coords.append(None)
        continue

    # Build A by stacking (I - v v^T) @ R_k
    A_blocks = []
    I3 = np.eye(3)
    for ray, Rk in zip(vs, Rmats):
        v = ray.reshape(3,1)
        P = I3 - (v @ v.T)    # 3x3
        A_block = P @ Rk      # 3x3
        A_blocks.append(A_block)
    A = np.vstack(A_blocks)   # (3*num_scans) x 3

    # Solve A p0 = 0 using SVD: p0 is right singular vector for smallest singular value
    try:
        U, S, Vt = np.linalg.svd(A)
        p0 = Vt[-1, :]
        # scale p0 so its z is positive and reasonable; keep as-is (up to scale)
        # We can attempt to resolve scale by enforcing that for first scan p_k = R_k p0 should lie on ray with positive scale:
        # compute scale for first scan
        R0 = Rmats[0]
        pk0 = R0 @ p0
        # compute alpha so that alpha * ray ≈ p_k -> alpha = dot(p_k, ray)
        alpha = float(np.dot(pk0, vs[0]))
        # scale p0 so that p_k aligns with alpha along ray
        if abs(alpha) > 1e-6:
            p0 = p0 / alpha
        three_d_coords.append([float(p0[0]), float(p0[1]), float(p0[2])])
    except Exception as e:
        three_d_coords.append(None)

# Save 3D coordinates
out = {
    "angles": angles,
    "num_leds": NUM_LEDS,
    "detections_2d": coords_by_scan,
    "coordinates_3d": three_d_coords
}
with open(os.path.join(save_dir, "savedata_3d.json"), "w") as f:
    json.dump(out, f, indent=2)

print("Saved 2D and 3D data to coordinates/")
