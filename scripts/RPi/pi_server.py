import socket
import json
import time
from rpi_ws281x import PixelStrip, Color
import threading
import math

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
NUM_LEDS_INITIAL = 600
NUM_LEDS_PER_STRIP = 200
strip1 = PixelStrip(NUM_LEDS_INITIAL, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip2 = PixelStrip(NUM_LEDS_INITIAL, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip3 = PixelStrip(NUM_LEDS_INITIAL, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip1.begin()
strip2.begin()
strip3.begin()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

print("Listening for LED frames on UDP port", UDP_PORT)

def show_all():
    t1 = threading.Thread(target=strip1.show)
    t2 = threading.Thread(target=strip2.show)
    t3 = threading.Thread(target=strip3.show)

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

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
                
                LED_indx = i % NUM_LEDS_PER_STRIP

                strip_number_str = str(math.floor(float(i / NUM_LEDS_PER_STRIP)))

                match strip_number_str:
                    case "0":
                        strip1.setPixelColor(LED_indx, Color(r, g, b))
                    case "1":
                        strip2.setPixelColor(LED_indx, Color(r, g, b))
                    case "2":
                        strip3.setPixelColor(LED_indx, Color(r, g, b))

            show_all()

        except BlockingIOError:
            # No data received
            time.sleep(0.01)
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)

except KeyboardInterrupt:
    print("Exiting, turning off LEDs")
    for i in range(NUM_LEDS_PER_STRIP):
        strip1[i] = (0, 0, 0)
        strip2[i] = (0, 0, 0)
        strip3[i] = (0, 0, 0)
    show_all()
