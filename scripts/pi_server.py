import socket
import json
import time
from rpi_ws281x import PixelStrip, Color

# =============================
# CONFIGURATION
# =============================
UDP_IP = "0.0.0.0"  # listen on all interfaces
UDP_PORT = 5005

LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

# Initialize with some default length; will adjust per frame
NUM_LEDS_INITIAL = 50
strip = PixelStrip(NUM_LEDS_INITIAL, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# =============================
# SETUP UDP SOCKET
# =============================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

print("Listening for LED frames on UDP port", UDP_PORT)

# =============================
# MAIN LOOP
# =============================
try:
    while True:
        try:
            data, addr = sock.recvfrom(65536)
            message = json.loads(data.decode())
            frame = message.get("frame", [])

            # Adjust strip length if frame size differs
            if len(frame) != strip.numPixels():
                strip = PixelStrip(len(frame), LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
                strip.begin()

            # Update LEDs
            for i, color in enumerate(frame):
                r, g, b = color
                strip.setPixelColor(i, Color(r, g, b))
            strip.show()

        except BlockingIOError:
            # No data received
            time.sleep(0.01)
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)

except KeyboardInterrupt:
    print("Exiting, turning off LEDs")
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
