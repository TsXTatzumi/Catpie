import snowboythreaded
import sys
import signal
import time
import os
import wave
import Queue
import subprocess

# This a demo that shows running Catpie in another thread
    
def actionCallback(action):
    actions.put(action)



def detectedCallback():
    print('recording audio...')


def signal_handler(signal, frame):
    stop_program = True

def pie():
    
    global stop_program
    stop_program = False

    global actions
    actions = Queue.Queue()
    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize ThreadedDetector object and start the detection thread
    threaded_detector = snowboythreaded.ThreadedDetector(sensitivity=[])
    threaded_detector.start()

    # main loop
    threaded_detector.start_recog(detected_callback=detectedCallback,
                                  action_callback=actionCallback,
                                  sleep_time=0.03)

    # Let audio initialization happen before requesting input
    time.sleep(1)

    # Do a simple task separate from the detection - addition of numbers
    while not stop_program:
        action = actions.get()
        print action
        subprocess.call(action)

    threaded_detector.terminate()


