import threading
import time

import math

def run_task_1():
    print("starting task 1")
    time.sleep(0.5)
    print("task 1 complete")

def run_task_2():
    print("starting task 2")
    time.sleep(0.5)
    print("task 2 complete")

thread1 = threading.Thread(target = run_task_1)
thread2 = threading.Thread(target = run_task_2)

thread1.start()
thread2.start()

thread1.join()
thread2.join()

NUM_LEDS_PER_STRIP = 10
i=22

strip_number_str = str(math.floor(float(i / NUM_LEDS_PER_STRIP)))

match strip_number_str:
    case "0":
        print("0")
    case "1":
        print("1")
    case "2":
        print("2")