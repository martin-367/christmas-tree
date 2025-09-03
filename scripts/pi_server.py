import socket
import json
import board
import neopixel

NUM_LEDS = 50
pixels = neopixel.NeoPixel(
    board.D18, NUM_LEDS, auto_write=True, brightness=0.2, pixel_order=neopixel.GRB
)

pixels.fill((0,0,0))
pixels.show()

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("Listening for UDP frames...")

while True:
    data, addr = sock.recvfrom(65536)
    try:
        msg = json.loads(data.decode())
        frame = msg["frame"]
        for i, color in enumerate(frame):
            pixels[i] = tuple(color)
    except Exception as e:
        print("Bad packet:", e)
