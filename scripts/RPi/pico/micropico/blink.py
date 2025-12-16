from machine import ADC, Pin
import time

# --- SETUP ---
# Potentiometer on GP26 (Pin 31)
pot = ADC(Pin(26))

# Button on GP15 (Pin 20)
# Pin.PULL_UP keeps the signal "High" (3.3V) when NOT pressed.
# When pressed, it connects to GND and goes "Low" (0V).
button = Pin(15, Pin.IN, Pin.PULL_UP)

conversion_factor = 3.3 / 65535

print("Ready! Twist the knob or press the button.")

while True:
    # 1. Read Potentiometer
    pot_raw = pot.read_u16()
    voltage = pot_raw * conversion_factor
    percent = (pot_raw / 65535) * 100
    
    # 2. Read Button
    # value() returns 0 if pressed (GND), 1 if not pressed (3.3V)
    if button.value() == 0:
        button_state = "PRESSED! [X]"
    else:
        button_state = "Released [ ]"
    
    # 3. Print everything on one line
    print(f"Knob: {percent:.1f}% | Voltage: {voltage:.1f}V | Button: {button_state}", end="\r")
    
    time.sleep(0.1)