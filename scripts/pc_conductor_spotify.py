import sounddevice as sd
import aubio
import socket
import json
import colorsys
import random

UDP_IP = "ledpi.local"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

NUM_LEDS = 50
FADE_STEPS = 8

# --- Beat detection ---
samplerate = 44100
win_s = 1024
hop_s = 512
tempo_detector = aubio.tempo("default", win_s, hop_s, samplerate)

# --- Color helper ---
def hsv_to_rgb_int(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return [int(r*255), int(g*255), int(b*255)]

def create_frame(intensity=1.0, hue=0.0, flash=False):
    frame = []
    for _ in range(NUM_LEDS):
        if flash and random.random() < 0.1:
            frame.append([255, 255, 255])
        else:
            frame.append(hsv_to_rgb_int(hue, 1.0, intensity))
    return frame

hue = 0.0

def audio_callback(indata, frames, time, status):
    global hue
    mono = indata.mean(axis=1).astype('float32')
    if tempo_detector(mono):
        # Beat detected
        hue = (hue + 0.1) % 1.0
        for step in range(FADE_STEPS, 0, -1):
            intensity = step / FADE_STEPS
            flash = random.random() < 0.2
            frame = create_frame(intensity=intensity, hue=hue, flash=flash)
            sock.sendto(json.dumps({"frame": frame}).encode(), (UDP_IP, UDP_PORT))

with sd.InputStream(channels=2, callback=audio_callback, samplerate=samplerate, blocksize=hop_s):
    print("Listening for beats...")
    import time
    while True:
        time.sleep(1)
