import threading
import time

def run_task_1():
    print("starting task 1")
    time.sleep(2)
    print("task 1 complete")

def run_task_2():
    print("starting task 2")
    time.sleep(2)
    print("task 2 complete")

thread1 = threading.Thread(target = run_task_1)
thread2 = threading.Thread(target = run_task_2)

thread1.start()
thread2.start()

thread1.join()
thread2.join()