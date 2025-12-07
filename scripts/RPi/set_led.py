import sys
import board, neopixel
import math

NUM_LEDS_PER_STRIP = 200
strip1 = neopixel.NeoPixel(board.D18, NUM_LEDS_PER_STRIP, brightness = 1.0, auto_write=False)
strip2 = neopixel.NeoPixel(board.D21, NUM_LEDS_PER_STRIP, brightness = 1.0, auto_write=False)
strip3 = neopixel.NeoPixel(board.D18, NUM_LEDS_PER_STRIP, brightness = 1.0, auto_write=False)

i = int(sys.argv[1]) # read LED index

strip_number_str = str(math.floor(float(i / NUM_LEDS_PER_STRIP)))

strip1.fill(color(0,0,0))
strip2.fill(color(0,0,0))
strip3.fill(color(0,0,0))

LED_indx = i % NUM_LEDS_PER_STRIP

match strip_number_str:
    case "0":
        strip1[LED_indx] = (255, 255, 255)
    case "1":
        strip2[LED_indx] = (255, 255, 255)
    case "2":
        strip3[LED_indx] = (255, 255, 255)
