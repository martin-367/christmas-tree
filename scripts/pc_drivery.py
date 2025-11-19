import soundcard as sc
import aubio
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
sparklesProbability = 0.4  # probability of sudden flash

# =============================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

samplerate = 44100
win_s = 1024
hop_s = 512
tempo_detector = aubio.tempo("default", win_s, hop_s, samplerate)

energy_history = []
current_mode = None
mode_start_time = 0
min_mode_duration = 2.0  # seconds - thisis adjusted in code

def strong_beat_detected(mono, energy, average_energy):
    return energy > 1.5 * average_energy


def averageEnergy(mono_chunk, RMS_energy):
    global energy_history
    
    energy_history.append(RMS_energy)
    if len(energy_history) > 43: # keep last 43 energies (~1 second at 512 hop size and 44100 Hz)
        # 43 is around 0.5 seconds of audio - CHECK
        energy_history.pop(0)
    
    average = np.mean(energy_history)
 
    return average

def add_sparkes(frame, intensity = 0.3, chance = 0.05):
    new_frame = frame.copy()
    random_color = [random.randint(100,255) for _ in range(3)]
    for i in range(len(frame)):
        if random.random() < chance:
            new_frame[i] = random_color # small white particle
    return new_frame

def color_wave(frame):
    new_frame = frame.copy()
    for i in range(len(frame)):
        hue = (i / len(frame) + time.time() * 0.1) % 1.0
        rgb = colorsys.hsv_to_rgb(hue, 1, 1)
        new_frame[i] = [int(c * 255) for c in rgb]
    return new_frame

def pulse(frame):
    new_frame = frame.copy()
    brightness = (0.5 + 0.5 * math.sin(time.time() * 2))
    for i in range(len(frame)):
        new_frame[i] = [int(c * brightness) for c in new_frame[i]]
    return new_frame

def random_colors():
    new_frame = []
    for i in range(NUM_LEDS):
        new_frame.append([random.randint(0,255) for _ in range(3)])
    return new_frame

def apply_fade_trail(prev_frame, new_frame, fade_factor=0.8):
    """
    Combines previous frame with new frame to create a fading trail.
    fade_factor: amount of previous frame to keep (0 → none, 1 → fully persistent)
    """
    frame = []
    for old, new in zip(prev_frame, new_frame):
        r = int(fade_factor * old[0] + (1 - fade_factor) * new[0])
        g = int(fade_factor * old[1] + (1 - fade_factor) * new[1])
        b = int(fade_factor * old[2] + (1 - fade_factor) * new[2])
        frame.append([r, g, b])
    return frame


def flash(frame):
    new_frame = frame.copy()
    random_color = [random.randint(100,255) for _ in range(3)]
    for i in range(len(frame)):
        new_frame[i] = random_color # small white particle
    return new_frame

prev_frame = [[0, 0, 0] for _ in range(NUM_LEDS)]

def audio_callback(indata):

    global prev_frame, current_mode, mode_start_time

    if status:
        print("Audio status:", status)

    now = time.time()

    mono = np.mean(indata, axis=1).astype('float32') # collapses stereo to mono

    energy = np.sqrt(np.mean(mono**2)) # RMS energy
    fft_vals = np.fft.rfft(mono)
    bass_energy = np.abs(fft_vals[:len(fft_vals)//4]).mean()  # lowest quarter of FFT
    avgEnergy = averageEnergy(mono, energy)
    frame = []
    for i in range(NUM_LEDS):
        frame.append([0, 0, 0])
    
    # append LED colors to frame

    sparkles = False

    if strong_beat_detected(mono, energy, avgEnergy):
        final_frame = flash(frame, intensity=0.5)
    
    else:
        if not tempo_detector(mono, energy):
            if energy < 0.7 * avgEnergy: # very low energy
                if current_mode is None or (now - mode_start_time) > min_mode_duration:
                    current_mode = random.choice(['color_wave', 'pulse'])
                    if random.random() < sparklesProbability:
                        sparkles = True
                    mode_start_time = now

                if current_mode == 'color_wave':
                    frame = color_wave(frame)
                elif current_mode == 'pulse':
                    frame = pulse(frame)
                
                
                if sparkles:
                    frame = add_sparkes(frame, chance=0.02) # only when energy is low - add this in

        else:
            frame = random_colors()
        
        
        final_frame = apply_fade_trail(prev_frame, frame, fade_factor=0.7)
        

    try:
        sock.sendto(json.dumps({"frame": final_frame}).encode(), (UDP_IP, UDP_PORT))
    except Exception as e:
        print("UDP send error:", e)

    prev_frame = final_frame.copy()

    

# --- Main Loop ---
print("Starting music-reactive lights. Press Ctrl+C to stop.")
try:
    # Get default loopback device (what you hear)
    with sc.default_speaker().recorder(samplerate=samplerate, blocksize=hop_s) as mic:
        while True:
            data = mic.record(numframes=hop_s)
            audio_callback(data)
except KeyboardInterrupt:
    print("Stopped by user")
except Exception as e:
    print("Error:", e)
