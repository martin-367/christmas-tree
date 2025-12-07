from matplotlib import pyplot as plt
import cv2
import os
import numpy as np
import json


CAPTURE_DIR = "led_images"  # Directory where images are stored
SAVE_DIR = "coordinates"
angles = [0, 45, 90, 135, 180, 225, 270, 315]  # Angles of the rig during capture
blurAmount = 41  # Gaussian blur kernel size, must be an odd number
num_LEDs = 50  # Total number of LEDs to process


class Point:
  def __init__(self, index, capture_dir, angles):
    self.index = index
    self.image_paths = {
      angle: os.path.join(capture_dir, f'led_{index}_angle_{angle}.png')
      for angle in angles
    }
    # the positions of the x values
    self.ix = []
    # the position of the y values
    self.iy = []
    # the weights (brightness)
    self.iw = []

    self.coords_3d = None

  def __str__(self):
     return f"Point: index={self.index}"

  def calculate_weighted_average_y(self):
    if not self.iw or sum(self.iw) == 0:
        return None
    weighted_y_sum = sum(y * w for y, w in zip(self.iy, self.iw))
    total_weight = sum(self.iw)
    return weighted_y_sum / total_weight

  def printVals(self):
    print(self)


Points = [Point(i, CAPTURE_DIR, angles) for i in range(num_LEDs)]


def triangulate_3d_coords(x_coords, weights, angles_deg):
    """
    Calculates the 3D coordinates (x, y, z) of a point from multiple 2D projections.
    This implementation assumes an orthographic projection where the camera rotates
    around the y-axis.
    """
    if len(x_coords) < 2 or sum(weights) == 0:
        return None, None

    angles_rad = np.deg2rad(angles_deg)
    
    # horizontal image coordinate 'x' as: x = r * cos(theta - alpha)
    # This can be expanded to: x = r * cos(theta) * cos(alpha) + r * sin(theta) * sin(alpha)
    # Let A = r * cos(theta) and B = r * sin(theta). Then x = A*cos(alpha) + B*sin(alpha)
    # We can solve for A and B using weighted least squares.
    M = np.vstack([np.cos(angles_rad), np.sin(angles_rad)]).T
    W = np.diag(weights)
    A, B = np.linalg.inv(M.T @ W @ M) @ M.T @ W @ x_coords
    return A, B


def detect_led_in_frame(image_path):
  image = cv2.imread(image_path)
  if image is None:
      print(f"Warning: Could not read image from {image_path}")
      return None, 0, None, (None, None)

  orig = image.copy()
  gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
  gray = cv2.GaussianBlur(gray, (blurAmount, blurAmount), 0)
  minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray)
  return minVal, maxVal, minLoc, maxLoc

for pnt in Points:
  # Center the x-coordinates relative to the image width
  # We need to read one image to get its dimensions.
  first_image_path = pnt.image_paths[angles[0]]
  first_image = cv2.imread(first_image_path)
  if first_image is None:
      print(f"Warning: Could not read first image for point {pnt.index} to get dimensions. Skipping point.")
      continue
  image_width = first_image.shape[1]
  center_x = image_width / 2

  for angle in angles:
    image_path = pnt.image_paths[angle]
    _minVal, maxVal, _minLoc, (maxLoc_x, maxLoc_y) = detect_led_in_frame(image_path)

    if maxLoc_x is not None:
      pnt.ix.append(maxLoc_x - center_x)
      pnt.iy.append(maxLoc_y)
      pnt.iw.append(maxVal)

  # Calculate 3D coordinates
  y_3d = pnt.calculate_weighted_average_y()
  x_3d, z_3d = triangulate_3d_coords(pnt.ix, pnt.iw, angles)

  if x_3d is not None and y_3d is not None and z_3d is not None:
      pnt.coords_3d = (x_3d, y_3d, z_3d)
      print(f"Point {pnt.index}: (X={x_3d:.2f}, Y={y_3d:.2f}, Z={z_3d:.2f})")


# --- Plotting ---
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(projection='3d')

coords = np.array([p.coords_3d for p in Points if p.coords_3d is not None])
x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]

ax.scatter(x, y, z)
ax.set_title("3D Map of LED Positions")
ax.set_xlabel("X coordinate")
ax.set_ylabel("Y coordinate")
ax.set_zlabel("Z coordinate")
plt.show()

# --- Saving Coordinates ---
os.makedirs(SAVE_DIR, exist_ok=True)
save_path = os.path.join(SAVE_DIR, "savedata.json")
print(f"Saving 3D coordinates to {save_path}")

# Convert numpy array to a list for JSON serialization
with open(save_path, "w") as save_file:
    json.dump(coords.tolist(), save_file, indent=6)
print("Coordinates saved successfully.")