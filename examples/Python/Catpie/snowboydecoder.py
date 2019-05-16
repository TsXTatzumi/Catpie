#!/usr/bin/env python

import collections
import pyaudio
import snowboydetect
import time
import wave
import sys
import keyboard
import threading
import logging
import os
from os import system, name 
from ctypes import *
from contextlib import contextmanager

logging.basicConfig()
logger = logging.getLogger("snowboy")
logger.setLevel(logging.INFO)
TOP_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(TOP_DIR, 'resources/models/')
RESOURCE_FILE = os.path.join(TOP_DIR, "resources/common.res")
DETECT_DING = os.path.join(TOP_DIR, "resources/ding.wav")
DETECT_DONG = os.path.join(TOP_DIR, "resources/dong.wav")

def py_error_handler(filename, line, function, err, fmt):
    pass

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def no_alsa_error():
    try:
        asound = cdll.LoadLibrary('libasound.so')
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield
        pass

class RingBuffer(object):
    """Ring buffer to hold audio from PortAudio"""
    def __init__(self, size = 4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        """Adds data to the end of buffer"""
        self._buf.extend(data)

    def get(self):
        """Retrieves data from the beginning of buffer and clears it"""
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp


def play_audio_file(fname=DETECT_DING):
    """Simple callback function to play a wave file. By default it plays
    a Ding sound.

    :param str fname: wave file name
    :return: None
    """
    ding_wav = wave.open(fname, 'rb')
    ding_data = ding_wav.readframes(ding_wav.getnframes())
    with no_alsa_error():
        audio = pyaudio.PyAudio()
    stream_out = audio.open(
        format=audio.get_format_from_width(ding_wav.getsampwidth()),
        channels=ding_wav.getnchannels(),
        rate=ding_wav.getframerate(), input=False, output=True)
    stream_out.start_stream()
    stream_out.write(ding_data)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    audio.terminate()
    
    
# define our clear function 
def clear(): 
  
    # for windows 
    if name == 'nt': 
        _ = system('cls') 
  
    # for mac and linux(here, os.name is 'posix') 
    else: 
        _ = system('clear')
  

inputstr = ""
once = ""

def setInput(val):
    global inputstr
    global once
        
    if val == "esc" or val == "enter":
        if True:
            inputstr = val
    else:
        inputstr = val
    
def init_hotkeys():
    keyboard.add_hotkey('up', setInput, args=['up'])
    keyboard.add_hotkey('down', setInput, args=['down'])
    keyboard.add_hotkey('left', setInput, args=['left'])
    keyboard.add_hotkey('right', setInput, args=['right'])
    keyboard.add_hotkey('enter', setInput, args=['enter'])
    keyboard.add_hotkey('escape', setInput, args=['esc'])
    
    
def store_sensitivities(models, new_sensitivityValues):
    
    sensitivities = [] 

    with open(MODEL_DIR + 'sensitivities.cfg') as sensitivityFile:
        sensitivities = [sensitivity.rstrip('\n') for sensitivity in sensitivityFile]
        sensitivities = [sensitivity.replace(' ', '').split(':') for sensitivity in sensitivities]
        
        
        for i in range (0, len(models)):

            found = False 
            for sensitivity in sensitivities:

                found = False
                
                if models[i] == sensitivity[0]:
                    found = True 
                    break
                
            if not found:
                sensitivities.append([models[i], 0.5])
        
            
        for i in range (0, len(sensitivities)):
            
            if sensitivities[i][0] in models:
                index = models.index(sensitivities[i][0])
                    
                sensitivities[i][1] = new_sensitivityValues[index]
        
    
    with open(MODEL_DIR + 'sensitivities.cfg', "w") as sensitivityFile:
        
        for i in range (0, len(sensitivities)):
            
            sensitivityFile.write(sensitivities[i][0]      + ":" \
                                + str(sensitivities[i][1]) + "\n")
                    
                    

class HotwordDetector(object):
    """
    Snowboy decoder to detect whether a keyword specified by `decoder_model`
    exists in a microphone input stream.

    :param decoder_model: decoder model file path, a string or a list of strings
    :param resource: resource file path.
    :param sensitivity: decoder sensitivity, a float of a list of floats.
                              The bigger the value, the more senstive the
                              decoder. If an empty list is provided, then the
                              default sensitivity in the model will be used.
    :param audio_gain: multiply input volume by this factor.
    :param apply_frontend: applies the frontend processing algorithm if True.
    """
    def __init__(self, decoder_model, decoder_actions,
                 resource=RESOURCE_FILE,
                 sensitivity=[],
                 audio_gain=1,
                 apply_frontend=False):

        def audio_callback(in_data, frame_count, time_info, status):
            self.ring_buffer.extend(in_data)
            play_data = chr(0) * len(in_data)
            return play_data, pyaudio.paContinue

        tm = type(decoder_model)
        ts = type(sensitivity)
        if tm is not list:
            decoder_model = [decoder_model]
        if ts is not list:
            sensitivity = [sensitivity]
        model_str = ",".join(decoder_model)
        
        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=resource.encode(), model_str=model_str.encode())
        self.detector.SetAudioGain(audio_gain)
        self.detector.ApplyFrontend(apply_frontend)
        self.num_hotwords = self.detector.NumHotwords()
        
        if len(decoder_model) > 1 and len(sensitivity) == 1:
            sensitivity = sensitivity*self.num_hotwords
        if len(sensitivity) != 0:
            assert self.num_hotwords == len(sensitivity), \
                "number of hotwords in decoder_model (%d) and sensitivity " \
                "(%d) does not match" % (self.num_hotwords, len(sensitivity))
        sensitivity_str = ",".join([str(t) for t in sensitivity])
        if len(sensitivity) != 0:
            self.detector.SetSensitivity(sensitivity_str.encode())
        
        self.ring_buffer = RingBuffer(
            self.detector.NumChannels() * self.detector.SampleRate() * 5)
        with no_alsa_error():
            self.audio = pyaudio.PyAudio()
        self.stream_in = self.audio.open(
                input=True, output=False,
                format=self.audio.get_format_from_width(
                    self.detector.BitsPerSample() / 8),
                channels=self.detector.NumChannels(),
                rate=self.detector.SampleRate(),
                frames_per_buffer=2048,
                stream_callback=audio_callback)
        try:
##            self.stream_in = self.audio.open(
##                input=True, output=False,
##                format=self.audio.get_format_from_width(
##                    self.detector.BitsPerSample() / 8),
##                channels=self.detector.NumChannels(),
##                rate=self.detector.SampleRate(),
##                frames_per_buffer=2048,
##                stream_callback=audio_callback)
            self.hasAudio = True
        except:
            self.hasAudio = False
        
        self.models = [model[len(MODEL_DIR):-5] for model in decoder_model]
        self.actions = decoder_actions
        self.sensitivities = sensitivity

    def start(self, detected_callback=play_audio_file,
              interrupt_check=lambda: False,
              sleep_time=0.03,
              action_callback=None,
              stop_callback=None,
              recording_timeout=5.0,
              further_keywords_timeout=1.0,
              calibrating=False):
        """
        Start the voice detector. For every `sleep_time` second it checks the
        audio buffer for triggering keywords. If detected, then call
        corresponding function in `detected_callback`, which can be a single
        function (single model) or a list of callback functions (multiple
        models). Every loop it also calls `interrupt_check` -- if it returns
        True, then breaks from the loop and return.

        :param detected_callback: a function or list of functions. The number of
                                  items must match the number of models in
                                  `decoder_model`.
        :param interrupt_check: a function that returns True if the main loop
                                needs to stop.
        :param float sleep_time: how much time in second every loop waits.
        :param audio_recorder_callback: if specified, this will be called after
                                        a keyword has been spoken and after the
                                        phrase immediately after the keyword has
                                        been recorded. The function will be
                                        passed the name of the file where the
                                        phrase was recorded.
        :param silent_count_threshold: indicates how long silence must be heard
                                       to mark the end of a phrase that is
                                       being recorded.
        :param recording_timeout: limits the maximum length of a recording.
        :param further_keywords_timeout: limits the maximum length of a recording
                                         after a matching voice-command was found.
        :return: None
        """
        global inputstr
        
        init_hotkeys()

        ####################################
        if interrupt_check():
            logger.debug("detect voice return")
            return

        tc = type(detected_callback)
        if tc is not list:
            detected_callback = [detected_callback]
        if len(detected_callback) == 1 and self.num_hotwords > 1:
            detected_callback *= self.num_hotwords

        assert self.num_hotwords == len(detected_callback), \
            "Error: hotwords in your models (%d) do not match the number of " \
            "callbacks (%d)" % (self.num_hotwords, len(detected_callback))

        ####################################
        logger.debug("detecting...")

        if calibrating:
            state = "CALIBRATING"
            global once
            
            model_strings = ["*SILENCE*", "WAKEWORD"]
            for i in range(1, len(self.models)):
                model_strings.append("Keyword: " + self.models[i])
            
            calibrationResults = []
            for i in range(0, len(self.models)):
                calibrationResults.append([0.0, 0.0])
                
            cursorRow = 0
            dotcount = 0
            timestampTimeout = 0
            lastWord = 0
        else:
##            action_callback(["pigs", "modes","5", "w"])
            state = "PASSIVE"
            
        clear()
        
        self.numThreads = threading.activeCount()
        
        while True:
            
            if interrupt_check() or not self.numThreads == threading.activeCount():
                logger.debug("detect voice break")
                break
            
            data = self.ring_buffer.get()

            if len(data) == 0:
                time.sleep(sleep_time)
                continue
            
            status = self.detector.RunDetection(data)
            if status == -1:
                logger.warning("Error initializing streams or reading audio data")
            
        ####################################
            #small state machine to handle recording of phrase after keyword
            if state == "PASSIVE":
                if status == 1: #wakeword found
                    keywords = []
                    timestampStartListening  = time.time()
                    timestampEndListening  = timestampStartListening + recording_timeout
                    messageLine1 = "WAKEWORD detected at time: "
                    messageLine2 = ""
                    messageLine1 += time.strftime("%Y-%m-%d %H:%M:%S",
                                         time.localtime(time.time()))
                    logger.info(messageLine1)
                    
                    clear()
                    sys.stdout.write(messageLine1)
                    sys.stdout.flush()
                    
                    callback = detected_callback[status-1]
                    if callback is not None:
                        callback()
                    
##                    action_callback(["pigs", "w","5", "1"])
                    state = "ACTIVE"
                    continue
                
                if inputstr == "esc" :
                    store_sensitivities(self.models, self.sensitivities)
                    stop_callback("exit")

                inputstr = ""
                once = False

        ####################################
            elif state == "ACTIVE":
                
                listening = True
                
                if timestampEndListening < time.time():
                    listening = False

                if listening == False:
                    
                    for action in self.actions:
                        if sorted(keywords) == sorted(action[0]):
                            action_callback(action[1])
                    
                    logger.info(messageLine2)
                    
                    clear()
                    sys.stdout.write(messageLine1)
                    sys.stdout.write("\n")
                    sys.stdout.write(messageLine2)
                    sys.stdout.flush()
                    
##                    action_callback(["pigs", "w","5", "0"])
                    state = "PASSIVE"
                    continue

                if status == 1: # WAKEWORD found - reset
                    keywords = []
                    
                if status > 1: #keyword found
                    timestampEndListening = timestampStartListening + recording_timeout
                    
                    keywords.append(status)
                    
                    messageLine2 = "["
                    for key in keywords:
                        if messageLine2 != "[":
                            messageLine2 += ", "
                            
                        messageLine2 += self.models[key - 1]
                    
                    messageLine2 += "]"
                    
                    for action in self.actions:
                        if sorted(keywords) == sorted(action[0]):
                            timestampEndListening = timestampStartListening + further_keywords_timeout
                            messageLine2 += "  ->  " + str(action[1])
                    
                    clear()
                    sys.stdout.write(messageLine1)
                    sys.stdout.write("\n")
                    sys.stdout.write(messageLine2)
                    sys.stdout.flush()
                
                if inputstr == "esc":
                    store_sensitivities(self.models, self.sensitivities)
                    stop_callback("exit")

                inputstr = ""
            
        ####################################
            elif state == "CALIBRATING":
                
                if inputstr == "up":
                    cursorRow = max(cursorRow - 1, 0)
                elif inputstr == "down":
                    cursorRow = min(cursorRow + 1, len(self.models) - 1)

                elif inputstr == "left":
                    self.sensitivities[cursorRow] = max(self.sensitivities[cursorRow] - 0.003, 0.0)
                elif inputstr == "right":
                    self.sensitivities[cursorRow] = min(self.sensitivities[cursorRow] + 0.003, 1.0)

                elif inputstr == "enter":
                    store_sensitivities(self.models, self.sensitivities)
                    stop_callback("-reboot oven")
                elif inputstr == "esc":
                    store_sensitivities(self.models, self.sensitivities)
                    stop_callback("exit")

                inputstr = ""

                clear()
                    
                for i in range(0, len(self.models)):

                    if i == cursorRow:
                        sys.stdout.write("-> ")

                    sys.stdout.write("ID: " + str(i) + " \t" + self.models[i] + ":\t")
                 
                    if len(self.models[i]) < 7:
                        sys.stdout.write("\t")

                    if calibrationResults[i][0] > 0:
                        sys.stdout.write(str(round(calibrationResults[i][1] / calibrationResults[i][0] * 100, 1)) + "%  (" + str(calibrationResults[i][0]) + ")")
                    else:
                        sys.stdout.write("n/a  (" + str(calibrationResults[i][0]) + ")")
                    
                    sys.stdout.write("\t< " + str(self.sensitivities[i] * 100) + "% >\n")
                    
                sys.stdout.write("-------------------\n\n")
                
                if status < 0:
                    if dotcount > 0:
                        state = "ENTER CORRECT"
                        dotcount = 0
                        
                    sys.stdout.write(model_strings[lastWord] + "\n")
                    
                elif status == 0:
                    dotcount += 1
                    
                    sys.stdout.write("[" + ("." * dotcount) + "]\n")
                    
                    timestampTimeout = time.time() + recording_timeout
                    lastWord = 0
                    
                elif status > 0:
                    if dotcount > 0:
                        state = "ENTER CORRECT"
                        dotcount = 0
                    
                    sys.stdout.write(model_strings[status] + "\n")
                    
                    timestampTimeout = time.time() + recording_timeout
                    lastWord = status

                sys.stdout.flush()
                
         ####################################
            elif state == "ENTER CORRECT":
                
                if inputstr == "up":
                    cursorRow = max(cursorRow - 1, 0)
                elif inputstr == "down":
                    cursorRow = min(cursorRow + 1, len(self.models) - 1)

                elif inputstr == "enter":
                    calibrationResults[cursorRow][0] += 1
                    if (lastWord - 1) == cursorRow:
                        calibrationResults[cursorRow][1] += 1
                    
                    state = "CALIBRATING"
                    lastWord = 0
                elif inputstr == "esc" or timestampTimeout < time.time():
                    state = "CALIBRATING"
                    lastWord = 0
                    
                inputstr = ""
                
                if status == 0:
                    calibrationResults[cursorRow][0] += 1
                    if (lastWord - 1) == cursorRow:
                        calibrationResults[cursorRow][1] += 1
                    state = "CALIBRATING"
                    lastWord = 0
                
                clear()
                    
                for i in range(0, len(self.models)):

                    if i == cursorRow:
                        sys.stdout.write("-> ")

                    sys.stdout.write("ID: " + str(i) + " \t" + self.models[i] + "\n")
                    
                sys.stdout.write("-------------------\n\n")
                
                sys.stdout.write(model_strings[lastWord] + "\n")

                sys.stdout.flush()

        ####################################
        

    def terminate(self):
        """
        Terminate audio stream. Users cannot call start() again to detect.
        :return: None
        """
        if hasattr(self, "stream_in"):
            self.stream_in.stop_stream()
            self.stream_in.close()
        
        self.audio.terminate()




