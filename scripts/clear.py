import sys
import board, neopixel

NUM_LEDS = 50
pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, auto_write=True)

i = int(sys.argv[1]) # read LED index
print(i)
for j in range(i):
    pixels[j] = (0, 0, 0) # set LED i to red

pixels.show()