import socket
import json
import random
import numpy as np
import time
import math

# =============================
# CONFIGURATION
# =============================
UDP_IP = "192.168.1.107"
UDP_PORT = 5005

COORDS_FILE = "savedata_adjusted.json"

# Load LED coordinates and determine NUM_LEDS from them
try:
    with open(COORDS_FILE, 'r') as f:
        led_coords = np.array(json.load(f))
    NUM_LEDS = len(led_coords)
except FileNotFoundError:
    print(f"Error: Coordinate file not found at {COORDS_FILE}")
    exit(1)

# =============================
# FIRE EFFECT CONFIGURATION
# =============================
FRAME_RATE = 30

# --- Noise parameters to control the fire's appearance ---
# Lower scale = larger, slower flames. Higher scale = smaller, faster flames.
NOISE_SCALE_X = 1.5
NOISE_SCALE_Y = 1.0
NOISE_SCALE_Z = 1.5

# How fast the fire rises
TIME_SCALE = 0.6

# --- Spatial setup ---
y_coords = led_coords[:, 1]
min_y, max_y = np.min(y_coords), np.max(y_coords)
tree_height = max_y - min_y

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def simple_noise3(x, y, z):
    """
    Generates a procedural, continuous noise-like value between 0.0 and 1.0
    for a 3D point using a combination of sine waves.
    This avoids the need for an external noise library.
    """
    # Combine sine waves at different frequencies and offsets to create a complex pattern.
    # The specific multipliers are chosen to create a visually interesting, non-uniform flow.
    v1 = math.sin(x * 0.5 + y * 0.2 + z * 0.3)
    v2 = math.sin(x * 1.2 - y * 0.8 + z * 0.7)
    v3 = math.sin(x * 2.1 + y * 1.5 - z * 1.3)

    # Average the sine waves (each is -1 to 1) and normalize the result to a 0-1 range.
    # (v1+v2+v3) is from -3 to 3. Adding 3 makes it 0 to 6. Dividing by 6 makes it 0 to 1.
    return (v1 + v2 + v3 + 3.0) / 6.0

def heat_to_color(heat):
    """
    Maps a heat value (0.0 to 1.0) to a fire-like color.
    0.0 -> black
    ... -> red
    ... -> orange
    ... -> yellow
    1.0 -> white
    """
    heat = max(0, min(1, heat))
    if heat < 0.2:
        # Fade from black to dark red
        return [int(heat * 5 * 60), 0, 0]
    elif heat < 0.5:
        # Fade from dark red to bright red
        return [60 + int((heat - 0.2) / 0.3 * 195), 0, 0]
    elif heat < 0.8:
        # Fade from red to yellow
        g = int((heat - 0.5) / 0.3 * 255)
        return [255, g, 0]
    else:
        # Fade from yellow to white
        b = int((heat - 0.8) / 0.2 * 255)
        return [255, 255, b]

def generate_fire_frame(t):
    """
    Generates a single frame of the fire animation.
    't' is the current time, used to animate the noise.
    """
    frame = [[0, 0, 0] for _ in range(NUM_LEDS)]
    
    for i in range(NUM_LEDS):
        # Get LED's 3D coordinates
        x, y, z = led_coords[i]

        # Calculate noise value. The y-coordinate is offset by time to make the fire "rise".
        noise_val = simple_noise3(x * NOISE_SCALE_X,
                                  (y - t * TIME_SCALE) * NOISE_SCALE_Y,
                                  z * NOISE_SCALE_Z)

        # Make the fire stronger at the bottom and fade out towards the top
        # 'y_falloff' will be 1.0 at the bottom and 0.0 at the top.
        y_falloff = 1.0 - ((y - min_y) / tree_height)
        
        # The final "heat" is the noise value modulated by the vertical falloff.
        # We square the falloff to make the base of the fire hotter and more distinct.
        heat = noise_val * (y_falloff ** 2)

        frame[i] = heat_to_color(heat)
        
    return frame

# --- Main Loop ---
print("Starting fire effect. Press Ctrl+C to stop.")
start_time = time.time()
try:
    while True:
        current_time = time.time() - start_time
        
        # Generate the frame
        final_frame = generate_fire_frame(current_time)
        
        # Pack and send the data
        packet = bytearray([int(c) for color in final_frame for c in color])
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        
        # Wait to maintain the desired frame rate
        time.sleep(1.0 / FRAME_RATE)

except KeyboardInterrupt:
    print("Stopped by user")
except Exception as e:
    print("Error:", e)
finally:
    # Send a final black frame to turn off all LEDs
    print("Turning off LEDs.")
    black_frame = [[0, 0, 0] for _ in range(NUM_LEDS)]
    packet = bytearray([int(c) for color in black_frame for c in color])
    sock.sendto(packet, (UDP_IP, UDP_PORT))
    sock.close()