import sounddevice as sd
import socket
import json
import numpy as np
import time

# =============================
# CONFIGURATION
# =============================
UDP_IP = "192.168.1.107"
UDP_PORT = 5005

NUM_LEDS = 800

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

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

samplerate = 44100
# Use a smaller hop for lower latency / more responsiveness
win_s = 1024
hop_s = 256   # was 512

# --- State for flash hold ---
led_buffer = np.zeros((NUM_LEDS, 3), dtype=float)
last_send_time = 0.0

def audio_callback(indata, frames, time_info, status):

    global led_buffer, last_send_time

    if status:
        print("Audio status:", status)

    now = time.time()
    mono = np.mean(indata, axis=1).astype('float32') # collapses stereo to mono

    energy = np.sqrt(np.mean(mono**2)) # RMS energy

    if energy > 0.01:
        print("Lights ON")
        led_buffer[:] = 255

    # Limit update rate to ~30 FPS to prevent network/LED flooding
    if now - last_send_time > 0.033:
        # Clip to valid range and convert to bytes
        output_frame = np.clip(led_buffer, 0, 255).astype(int)
        packet = bytearray([c for pixel in output_frame for c in pixel])
        try:
            sock.sendto(packet, (UDP_IP, UDP_PORT))
        except Exception as e:
            print("UDP send error:", e)
        last_send_time = now
        led_buffer[:] = 0

# --- Main Loop ---
print("Starting music-reactive lights. Press Ctrl+C to stop.")
try:
    # get audio stream from system audio index
    with sd.InputStream(device=SYSTEM_AUDIO_INDEX,
                        channels=1, # 1 channel (stereo to mono as spatial sound isn't necessary)
                        samplerate=samplerate,
                        blocksize=hop_s,
                        callback=audio_callback): # audio_callack is called when a new block of audio is available
        while True:
            time.sleep(1)
except KeyboardInterrupt:
    print("Stopped by user")
except Exception as e:
    print("Error:", e)