from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
import math as maths
import numpy as np
import json
import os

save_dir = "coordinates"
os.makedirs(save_dir, exist_ok=True)


with open((os.path.join(save_dir, "savedata.json")), "r") as json_File :
    sample_load_file = json.load(json_File)

NUM_LEDS = np.size(sample_load_file, 0)

coords = sample_load_file

# --- Coordinate Normalization ---

# Convert to a NumPy array for easier manipulation
coords_np = np.array(coords)

# Separate the coordinates
x = coords_np[:, 0]
y = coords_np[:, 1]
z = coords_np[:, 2]

# Find the min/max for X and Y to determine the bounding box
x_min, x_max = np.min(x), np.max(x)
y_min, y_max = np.min(y), np.max(y)

# To maintain the aspect ratio, find the largest range between X and Y
xy_range = max(x_max - x_min, y_max - y_min)

# Normalize X and Y to be between -1 and 1, centered
x_normalized = -1 + 2 * (x - x_min) / xy_range
y_normalized = -1 + 2 * (y - y_min) / xy_range

# Scale Z proportionally, starting from 0
z_min = np.min(z)
z_scaled = (z - z_min) / xy_range

# Combine the adjusted coordinates
adjusted_coords = np.stack([x_normalized, y_normalized, z_scaled], axis=1)

# --- Save the adjusted coordinates ---
save_path = os.path.join(save_dir, "savedata_adjusted.json")
with open(save_path, "w") as f:
    json.dump(adjusted_coords.tolist(), f, indent=4)

print(f"Adjusted coordinates saved to {save_path}")

# --- Plotting the Adjusted Coordinates ---
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(projection='3d')

# Extract normalized coordinates for plotting
x_adj, y_adj, z_adj = adjusted_coords[:, 0], adjusted_coords[:, 1], adjusted_coords[:, 2]

ax.scatter(x_adj, y_adj, z_adj)
ax.set_title("3D Map of Adjusted LED Positions")
ax.set_xlabel("Normalized X")
ax.set_ylabel("Normalized Y")
ax.set_zlabel("Scaled Z")

# Set aspect ratio to be equal to avoid distortion
ax.set_aspect('equal', 'box')

plt.show()
