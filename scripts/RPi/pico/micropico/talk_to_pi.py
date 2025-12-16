from machine import UART, Pin, ADC
import time

uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# Initialize ADC on GP26 (ADC0)
potentiometer = ADC(26)

# Optional: Keep the button code if you still have it wired
button = Pin(15, Pin.IN, Pin.PULL_UP)

print("ADC Telemetry System Ready")

last_send_time = 0
conversion_factor = 3.3 / 65535


while True:
    current_time = time.ticks_ms()
    
    # --- Part A: Read Potentiometer ---
    # We use a timer check so we don't spam the Pi Zero 1000 times a second.
    # Sending every 200ms (5 times a second) is usually snappy enough.
    if time.ticks_diff(current_time, last_send_time) > 200:
        
        # Read raw 16-bit value (0 - 65535)
        raw_value = potentiometer.read_u16()
        voltage = raw_value * conversion_factor

        # Format: "key:value\n"
        message = "pot:{}\n".format(voltage)
        uart.write(message)
        
        last_send_time = current_time

    # --- Part B: Check Button (Instant trigger) ---
    if button.value() == 0:
        uart.write("btn:pressed\n")
        print(f"voltage is {voltage}")
        
        while button.value() == 0:
            time.sleep(0.01)

    time.sleep(0.01)