import sounddevice as sd
import socket
import json
import colorsys
import random
import numpy as np
import time
import math

# =============================
# CONFIGURATION
# =============================
UDP_IP = "192.168.1.107"
UDP_PORT = 5005

NUM_LEDS = 50

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

# Keep a shorter energy history so average reacts faster
energy_history = []

# track previous short-term energy to detect sudden rises
prev_energy = 0.0

# --- State for flash hold ---
last_flash_time = 0.0

def strong_beat_detected(mono, energy, average_energy):
    """
    Strong beat if energy is considerably above recent average OR
    if energy jump (derivative) is large.
    """
    global prev_energy
    energy_ratio = energy / (average_energy + 1e-9)
    energy_deriv = energy - prev_energy
    prev_energy = energy
    # thresholds tuned for responsiveness:
    return (energy_ratio > 1.7) or (energy_deriv > 0.03)

def is_beat_detected(energy, avg_energy):
    """Determines if the current energy constitutes a moderate beat."""
    return energy > 1.2 * avg_energy

def averageEnergy(mono_chunk, RMS_energy):
    global energy_history

    energy_history.append(RMS_energy)
    # shorter window to adapt faster to changes
    max_len = 20
    if len(energy_history) > max_len:
        energy_history.pop(0)

    average = np.mean(energy_history)
    return average

def flash(frame, intensity=1.0):
    """
    Create a short, bright flash with spatial falloff.
    intensity: 0.0..n - scales brightness
    """
    new_frame = [[0,0,0] for _ in range(len(frame))]
    # choose one or a few impact points for variety
    centers = [random.randint(0, len(frame)-1) for _ in range(random.choice([1,1,2]))]
    base_color = [random.randint(150, 255), random.randint(80, 220), random.randint(0, 120)]

    for c in centers:
        # scale controls how quickly it fades across LEDs
        scale = max(3, int(5 - intensity))  # stronger beats are tighter
        for i in range(len(frame)):
            dist = abs(i - c)
            # gaussian-like falloff
            fall = math.exp(- (dist**2) / (2 * (scale**2)))
            brightness = min(1.0, intensity * fall)
            r = int(base_color[0] * brightness)
            g = int(base_color[1] * brightness)
            b = int(base_color[2] * brightness)
            # additive so multiple centers can stack
            new_frame[i][0] = min(255, new_frame[i][0] + r)
            new_frame[i][1] = min(255, new_frame[i][1] + g)
            new_frame[i][2] = min(255, new_frame[i][2] + b)

    return new_frame

def audio_callback(indata, frames, time_info, status):

    global last_flash_time

    if status:
        print("Audio status:", status)

    now = time.time()
    mono = np.mean(indata, axis=1).astype('float32') # collapses stereo to mono

    energy = np.sqrt(np.mean(mono**2)) # RMS energy
    avgEnergy = averageEnergy(mono, energy)

    send_data = False
    final_frame = None

    # compute intensity proportional to how strong the beat is
    intensity = max(0.3, min(3.0, (energy / (avgEnergy + 1e-9))))
    if strong_beat_detected(mono, energy, avgEnergy):
        # stronger beats -> higher intensity and tighter flash
        intensity_scaled = intensity * 1.2
        final_frame = flash([[0,0,0]] * NUM_LEDS, intensity=intensity_scaled)
        send_data = True
        last_flash_time = now
        # Debug print for beat strength (can be commented out)
        print(f"Flash! energy={energy:.4f} avg={avgEnergy:.4f} ratio={energy/ (avgEnergy+1e-9):.2f}")
    elif (now - last_flash_time > 0.08) and (last_flash_time != 0):
        # If 80ms have passed since the last flash, send a black frame to clear.
        final_frame = [[0, 0, 0] for _ in range(NUM_LEDS)]
        send_data = True
        last_flash_time = 0 # Reset so we only send the black frame once.

    if send_data:
        packet = bytearray([int(c) for color in final_frame for c in color])
        try:
            sock.sendto(packet, (UDP_IP, UDP_PORT))
        except Exception as e:
            print("UDP send error:", e)

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