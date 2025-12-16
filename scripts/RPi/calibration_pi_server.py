import socket
import json
import time
from rpi_ws281x import PixelStrip, Color
import threading
import math
from collections import deque
import serial


# =============================
# CONFIGURATION
# =============================
UDP_IP = "0.0.0.0"  # listen on all interfaces
UDP_PORT = 5005
DISPLAY_DELAY = 0.2  # Delay in seconds

# LED strip configuration
LED_PIN_1 = 18        # PWM0
LED_PIN_2 = 21        # PCM_DOUT
LED_PIN_3 = 13        # SPI_MOSI
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False

# Initialize with some default length; will adjust per frame
NUM_LEDS_PER_STRIP = 200

# Use different channels for PWM-based strips if they share a PWM peripheral
strip1 = PixelStrip(NUM_LEDS_PER_STRIP, LED_PIN_1, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, channel=0)
strip2 = PixelStrip(NUM_LEDS_PER_STRIP, LED_PIN_2, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip3 = PixelStrip(NUM_LEDS_PER_STRIP, LED_PIN_3, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, channel=1)
strip1.begin()
strip2.begin()
strip3.begin()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

print("Listening for LED frames on UDP port", UDP_PORT)

frame_buffer = deque()


# /dev/serial0 is the default alias for the primary UART pins
ser = serial.Serial('/dev/serial0', 115200, timeout=1)
ser.reset_input_buffer()

print("Connecting to Pico...")


try:
    while True:
        try:
            data, addr = sock.recvfrom(65536)
            frame_buffer.append((time.time() + DISPLAY_DELAY, data))
        except BlockingIOError:
            pass

        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            try:
                DISPLAY_DELAY = float(line)
                print(f"Delay updated to: {DISPLAY_DELAY}")
            except ValueError:
                print(f"Pico said: {line}")

        if not frame_buffer or time.time() < frame_buffer[0][0]:
            time.sleep(0.001)
            continue

        _, data = frame_buffer.popleft()

        # The data is a flat byte array: [r,g,b,r,g,b,...]
        # We process it in chunks of 3 bytes.
        num_pixels = len(data) // 3
        for i in range(num_pixels):
            r = data[i*3]
            g = data[i*3 + 1]
            b = data[i*3 + 2]
            
            # Determine which strip and which LED on that strip to light up
            strip_index = i // NUM_LEDS_PER_STRIP
            led_index = i % NUM_LEDS_PER_STRIP
            
            if strip_index == 0:
                strip1.setPixelColor(led_index, Color(r, g, b))
            elif strip_index == 1:
                strip2.setPixelColor(led_index, Color(r, g, b))
            elif strip_index == 2:
                strip3.setPixelColor(led_index, Color(r, g, b))

        # Show strips sequentially; the library is not thread-safe
        strip1.show()
        strip2.show()
        strip3.show()
        print("Frame displayed")

except KeyboardInterrupt:
    ser.close()
    print("Exiting, turning off LEDs")
    for i in range(NUM_LEDS_PER_STRIP):
        strip1.setPixelColor(i, Color(0, 0, 0))
        strip2.setPixelColor(i, Color(0, 0, 0))
        strip3.setPixelColor(i, Color(0, 0, 0))
    strip1.show()
    strip2.show()
    strip3.show()
