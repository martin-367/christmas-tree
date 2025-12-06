import sys
import board, neopixel
import threading

NUM_LEDS_PER_STRING = 200
strip1 = neopixel.NeoPixel(board.D18, NUM_LEDS_PER_STRING, brightness = 1.0, auto_write=False)
strip2 = neopixel.NeoPixel(board.D21, NUM_LEDS_PER_STRING, brightness = 1.0, auto_write=False)
strip3 = neopixel.NeoPixel(board.D18, NUM_LEDS_PER_STRING, brightness = 1.0, auto_write=False)

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

for i in range(NUM_LEDS_PER_STRING):
    strip1[i] = (0, 0, 0) # set LED i to red
    strip2[i] = (0, 0, 0) # set LED i to red
    strip3[i] = (0, 0, 0) # set LED i to red

show_all()