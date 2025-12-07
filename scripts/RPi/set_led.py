import sys
import board, neopixel
import math
import threading

NUM_LEDS_PER_STRIP = 200
strip1 = neopixel.NeoPixel(board.D18, NUM_LEDS_PER_STRIP, brightness = 1.0, auto_write=False)
strip2 = neopixel.NeoPixel(board.D21, NUM_LEDS_PER_STRIP, brightness = 1.0, auto_write=False)
strip3 = neopixel.NeoPixel(board.D12, NUM_LEDS_PER_STRIP, brightness = 1.0, auto_write=False)

i = int(sys.argv[1]) # read LED index

strip_number_str = str(math.floor(float(i / NUM_LEDS_PER_STRIP)))
LED_indx = i % NUM_LEDS_PER_STRIP

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

# Clear all strips first
strip1.fill((0,0,0))
strip2.fill((0,0,0))
strip3.fill((0,0,0))

match strip_number_str:
    case "0":
        strip1[LED_indx] = (255, 255, 255)
    case "1":
        strip2[LED_indx] = (255, 255, 255)
    case "2":
        strip3[LED_indx] = (255, 255, 255)

# Push the update to the strips
show_all()
