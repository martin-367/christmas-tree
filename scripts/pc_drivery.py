import sounddevice as sd
import aubio
import socket
import json
import colorsys
import random
import numpy as np
import time

# =============================
# CONFIGURATION
# =============================
UDP_IP = "192.168.1.107"
UDP_PORT = 5005

NUM_LEDS = 50
BRIGHTNESS = 1.0
BASELINE_INTENSITY = 0.2  # minimum glow
FLASH_PROB = 0.3  # probability of sudden flash

# =============================
# DEVICE SELECTION
# =============================
def select_input_device():
    print("Available input devices:")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"{i}: {d['name']} (inputs={d['max_input_channels']})")
    idx = input("Enter device index to use for input: ")
    try:
        idx = int(idx)
        if devices[idx]['max_input_channels'] < 1:
            raise ValueError("Device does not support input.")
        return idx
    except Exception as e:
        print(f"Invalid selection: {e}")
        exit(1)

SYSTEM_AUDIO_INDEX = select_input_device()

# =============================
# SOCKET SETUP
# =============================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# =============================
# AUDIO ANALYSIS SETUP
# =============================
samplerate = 44100
win_s = 1024
hop_s = 512

# Beat detection (aubio)
tempo_detector = aubio.tempo("default", win_s, hop_s, samplerate)

# =============================
# HELPER FUNCTIONS
# =============================
def hsv_to_rgb_int(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return [int(r*255), int(g*255), int(b*255)]

def create_frame(intensity=1.0, hue=0.0, flash=False):
    frame = []
    for _ in range(NUM_LEDS):
        if flash and random.random() < FLASH_PROB:
            frame.append([255, 255, 255])
        else:
            frame.append(hsv_to_rgb_int(hue, 1.0, intensity))
    return frame

def calculate_centroid(fft_vals, freqs):
    magnitude = np.abs(fft_vals)
    if magnitude.sum() == 0:
        return 0
    return np.sum(freqs * magnitude) / np.sum(magnitude)

def calculate_flux(prev_fft, curr_fft):
    return np.sum((np.abs(curr_fft) - np.abs(prev_fft))**2)

# =============================
# AUDIO CALLBACK
# =============================
hue = 0.0
prev_fft = None

def audio_callback(indata, frames, time_info, status):
    global hue, prev_fft
    if status:
        print("Audio status:", status)

    # Mono
    mono = np.mean(indata, axis=1).astype('float32')

    # RMS energy → brightness
    energy = np.sqrt(np.mean(mono**2))
    brightness = BASELINE_INTENSITY + min(1.0, energy * 10) * (BRIGHTNESS - BASELINE_INTENSITY)

    # FFT
    fft_vals = np.fft.rfft(mono)
    freqs = np.fft.rfftfreq(len(mono), 1./samplerate)

    # Spectral centroid → hue
    hue = (calculate_centroid(fft_vals, freqs) / 5000.0) % 1.0

    # Spectral flux → extra flashes
    flash = False
    if prev_fft is not None:
        flux = calculate_flux(prev_fft, fft_vals)
        if flux > 0.05:  # adjust sensitivity
            flash = True
    prev_fft = fft_vals

    # Beat detection
    if tempo_detector(mono):
        flash = True

    # Turn off LEDs if very quiet
    if energy < 0.001:
        brightness = 0.0

    # Send frame to Pi
    frame = create_frame(intensity=brightness, hue=hue, flash=flash)
    try:
        sock.sendto(json.dumps({"frame": frame}).encode(), (UDP_IP, UDP_PORT))
    except Exception as e:
        print("UDP send error:", e)

# =============================
# START AUDIO STREAM
# =============================
print("Starting music-reactive lights. Press Ctrl+C to stop.")

try:
    with sd.InputStream(device=SYSTEM_AUDIO_INDEX,
                        channels=1,
                        samplerate=samplerate,
                        blocksize=hop_s,
                        callback=audio_callback):
        while True:
            time.sleep(1)
except KeyboardInterrupt:
    print("Stopped by user")
except Exception as e:
    print("Error:", e)
