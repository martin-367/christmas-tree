import sys
import board, neopixel

NUM_LEDS = 10
pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, auto_write=True)

i = int(sys.argv[1]) # read LED index
print(i)
pixels.fill((0, 0, 0)) # turn all off
pixels[i] = (255, 255, 255) # set LED i to red