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

# Keep a shorter energy history so average reacts faster
energy_history = []

# track previous short-term energy to detect sudden rises
prev_energy = 0.0

# --- State for flash hold ---
led_buffer = np.zeros((NUM_LEDS, 3), dtype=float)
last_send_time = 0.0

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

    # Generate a random vivid color using HSV
    hue = random.random()
    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    base_color = [int(c * 255) for c in rgb]

    for c in centers:
        # scale controls how quickly it fades across LEDs
        scale = random.randint(15, 40) # Wider flashes
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

def sparkle(frame, intensity=1.0):
    """Random LEDs light up."""
    new_frame = [[0,0,0] for _ in range(len(frame))]
    # Density depends on intensity
    count = int(len(frame) * (0.1 + 0.1 * min(3.0, intensity)))
    brightness = min(1.0, intensity)
    
    for _ in range(count):
        idx = random.randint(0, len(frame)-1)
        hue = random.random()
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        new_frame[idx] = [int(c * 255 * brightness) for c in rgb]
    return new_frame

def wipe(frame, intensity=1.0):
    """Lights up a random segment."""
    new_frame = [[0,0,0] for _ in range(len(frame))]
    segment_len = random.randint(100, 400)
    start = random.randint(0, max(0, len(frame) - segment_len))
    
    hue = random.random()
    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    brightness = min(1.0, intensity)
    base_color = [int(c * 255 * brightness) for c in rgb]
    
    for i in range(segment_len):
        if start + i < len(frame):
            new_frame[start+i] = base_color
    return new_frame

def audio_callback(indata, frames, time_info, status):

    global led_buffer, last_send_time

    if status:
        print("Audio status:", status)

    now = time.time()
    mono = np.mean(indata, axis=1).astype('float32') # collapses stereo to mono

    energy = np.sqrt(np.mean(mono**2)) # RMS energy
    avgEnergy = averageEnergy(mono, energy)

    # Decay the current state slowly so LEDs stay on longer
    led_buffer *= 0.92

    # compute intensity proportional to how strong the beat is
    intensity = max(0.3, min(3.0, (energy / (avgEnergy + 1e-9))))
    if strong_beat_detected(mono, energy, avgEnergy):
        # stronger beats -> higher intensity and tighter flash
        intensity_scaled = intensity * 1.2
        effect = random.choice([flash, flash, sparkle, wipe])
        effect_frame = effect([[0,0,0]] * NUM_LEDS, intensity=intensity_scaled)
        
        # Add the new effect on top of the existing buffer
        led_buffer += np.array(effect_frame)
        
        # Debug print for beat strength (can be commented out)
        print(f"Flash! energy={energy:.4f} avg={avgEnergy:.4f} ratio={energy/ (avgEnergy+1e-9):.2f}")

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