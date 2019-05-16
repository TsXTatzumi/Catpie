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

def stopCallback(todo):
    global threaded_detector
    
    if todo == "reboot oven":
       threaded_detector.pause_recog()
       threaded_detector.change_sensitivity(threaded_detector.load_sensitivities())
       threaded_detector.start_recog(detected_callback=detectedCallback,
                                      action_callback=actionCallback,
                                      stop_callback=stopCallback,
                                      sleep_time=0.03,
                                      calibrating=True)
    
    elif todo == "exit":
        actions.put("!")

def detectedCallback():
    print('recording audio...')


def signal_handler(signal, frame):
    stop_program = True

threaded_detector = None

def pie(state):
    
    global stop_program
    stop_program = False

    global actions
    actions = Queue.Queue()
    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize ThreadedDetector object and start the detection thread
    global threaded_detector
    threaded_detector = snowboythreaded.ThreadedDetector(sensitivity=[])
    threaded_detector.start()

    # main loop
    if state == "eat":
        threaded_detector.start_recog(detected_callback=detectedCallback,
                                      action_callback=actionCallback,
                                      stop_callback=stopCallback,
                                      recording_timeout=8.0,
                                      sleep_time=0.03)
    elif state == "bake":
        threaded_detector.start_recog(detected_callback=detectedCallback,
                                      action_callback=actionCallback,
                                      stop_callback=stopCallback,
                                      sleep_time=0.03,
                                      calibrating=True)
    else:
        stop_program = True

    # Let audio initialization happen before requesting input
    time.sleep(1)

    # Do a simple task separate from the detection - addition of numbers
    while not stop_program:
        action = actions.get()
        
        if action == "!":
            break
        
        subprocess.call(action)

    threaded_detector.terminate()


