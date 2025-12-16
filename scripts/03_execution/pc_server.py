import sounddevice as sd
import socket
import json
import colorsys
import random
import numpy as np
import time
import math
from collections import deque

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

def apply_fade_trail(prev_frame, new_frame, fade_factor=0.5):
    """
    Combines previous frame with new frame to create a fading trail.
    fade_factor: amount of previous frame to keep (0 → none, 1 → fully persistent)
    Lower fade_factor => faster decay (more responsive).
    """
    frame = []
    for old, new in zip(prev_frame, new_frame):
        r = int(fade_factor * old[0] + (1 - fade_factor) * new[0])
        g = int(fade_factor * old[1] + (1 - fade_factor) * new[1])
        b = int(fade_factor * old[2] + (1 - fade_factor) * new[2])
        frame.append([r, g, b])
    return frame

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

prev_frame = [[0, 0, 0] for _ in range(NUM_LEDS)]

# --- Tempo / metronome state ---
onset_times = deque(maxlen=32)
last_onset_time = 0.0
MIN_ONSET_INTERVAL = 0.18   # seconds - ignore onsets closer than this (debounce)
MIN_BPM = 40
MAX_BPM = 200
bpm = 0.0
BPM_SMOOTH = 0.85           # smoothing factor for BPM updates (higher => slower changes)
next_tick = 0.0
ALIGN_TOLERANCE = 0.12      # seconds - how close an onset must be to align phase
CLEAR_AFTER = 0.08          # seconds to wait before sending a clear (black) frame after a tick
last_flash_time = 0.0
last_sent_black = False

def estimate_bpm_from_onsets():
    global bpm, next_tick
    if len(onset_times) < 4:
        return
    diffs = np.diff(np.array(onset_times))
    # reject very long or very short intervals
    diffs = diffs[(diffs > 0.2) & (diffs < 2.0)]
    if len(diffs) < 3:
        return
    median_interval = np.median(diffs)
    if median_interval <= 0:
        return
    candidate_bpm = 60.0 / median_interval
    if candidate_bpm < MIN_BPM or candidate_bpm > MAX_BPM:
        return
    if bpm == 0.0:
        bpm = candidate_bpm
        next_tick = onset_times[-1] + (60.0 / bpm)
    else:
        bpm = BPM_SMOOTH * bpm + (1.0 - BPM_SMOOTH) * candidate_bpm

def schedule_and_emit_metronome(now, energy):
    """
    Check whether it's time to emit a metronome tick (flash).
    Returns (should_send, frame) where should_send is True when a packet should be sent.
    """
    global next_tick, last_flash_time, last_sent_black

    if bpm == 0.0:
        return False, None

    interval = 60.0 / bpm
    sent = False
    frame = None

    # If we haven't initialized next_tick (e.g. BPM learned but next_tick not set), set it
    if next_tick == 0.0:
        next_tick = now + interval

    # If an onset is close to the next tick, align phase
    # (Don't create a flash here — we'll flash at the aligned tick below)
    if abs(now - next_tick) < ALIGN_TOLERANCE:
        next_tick = now + interval

    # Emit ticks for any overdue intervals (catch up)
    while now >= next_tick:
        # Create the flash for this tick; intensity can be derived from recent energy
        intensity = max(0.6, min(2.5, (energy * 5.0)))  # scale energy to intensity
        frame = flash([[0,0,0]] * NUM_LEDS, intensity=intensity)
        last_flash_time = now
        last_sent_black = False
        sent = True
        next_tick += interval

    return sent, frame

def audio_callback(indata, frames, time_info, status):

    global prev_frame, last_onset_time, last_flash_time, last_sent_black

    if status:
        print("Audio status:", status)

    now = time.time()
    mono = np.mean(indata, axis=1).astype('float32') # collapses stereo to mono

    energy = np.sqrt(np.mean(mono**2)) # RMS energy
    avgEnergy = averageEnergy(mono, energy)

    # Update onset list if a strong onset detected (used for BPM estimation)
    if strong_beat_detected(mono, energy, avgEnergy):
        if (now - last_onset_time) > MIN_ONSET_INTERVAL:
            onset_times.append(now)
            last_onset_time = now
            estimate_bpm_from_onsets()
            # Align phase if this onset is very close to the expected tick
            if bpm != 0.0 and abs(now - next_tick) < ALIGN_TOLERANCE:
                # snap next tick to now and advance
                next_tick = now + (60.0 / bpm)

    # Only flash on metronome ticks (not on every onset)
    should_send, frame = schedule_and_emit_metronome(now, energy)

    # If a tick was emitted, send it and ensure a black frame gets sent shortly after
    if should_send and frame is not None:
        packet = bytearray([int(c) for color in frame for c in color])
        try:
            sock.sendto(packet, (UDP_IP, UDP_PORT))
        except Exception as e:
            print("UDP send error:", e)
        last_sent_black = False
        return

    # If enough time has passed since last flash, send a single black frame and then stop
    if (last_flash_time != 0.0) and (now - last_flash_time > CLEAR_AFTER) and (not last_sent_black):
        black_frame = [[0, 0, 0] for _ in range(NUM_LEDS)]
        packet = bytearray([int(c) for color in black_frame for c in color])
        try:
            sock.sendto(packet, (UDP_IP, UDP_PORT))
        except Exception as e:
            print("UDP send error:", e)
        last_sent_black = True
        # reset last_flash_time so we don't repeatedly clear
        last_flash_time = 0.0
        return

    # Otherwise do nothing (no packet) — metronome-only behavior
    return
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