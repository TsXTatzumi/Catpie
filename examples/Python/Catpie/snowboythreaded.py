import snowboydecoder
import threading
import Queue
import glob
import os
import time



TOP_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(TOP_DIR, 'resources/models/')
ACTION_DIR = os.path.join(TOP_DIR, 'resources/actions/')



class ThreadedDetector(threading.Thread):
    """
    Wrapper class around detectors to run them in a separate thread
    and provide methods to pause, resume, and modify detection
    """
    def load_models(self):
    
        models = []    
        wakewordFound = False
        dir = glob.glob(MODEL_DIR + '*')
    
        for f in dir:
            if(f.endswith(('.umdl', '.pmdl'))):
                if ('wakeword.umdl' == f[len(MODEL_DIR):].lower()) or ('wakeword.pmdl' == f[len(MODEL_DIR):].lower()):
                
                    assert not wakewordFound, \
                  'There can only be one wakeword file. Remove One!'
                
                    models.insert(0, f)
                    wakewordFound = True
                
                else:
                    models.append(f)
                    
    
        assert wakewordFound, \
      'There must be one wakeword file. Add One!'
        
        return models

    def load_sensitivities(self):
    
        sensitivities = [] 
        sensitivityValues = []
    
        with open(MODEL_DIR + 'sensitivities.cfg') as sensitivityFile:
            sensitivities = [sensitivity.rstrip('\n') for sensitivity in sensitivityFile]
            sensitivities = [sensitivity.replace(' ', '').split(':') for sensitivity in sensitivities]
            models = [model[len(MODEL_DIR):-5] for model in self.models]
            
            
            for i in range (0, len(models)):

                found = False 
                for sensitivity in sensitivities:

                    found = False
                    
                    if models[i] == sensitivity[0]:
                        sensitivityValues.append(float(sensitivity[1]))
                        found = True 
                        break
                    
                if not found:
                    sensitivityValues.append(0.5)
            
            return sensitivityValues
    
    def load_actions(self):
    
        actions = []
    
        with open(ACTION_DIR + 'actions.cfg') as actionFile:
            actions = [action.rstrip('\n') for action in actionFile]
            actions = [action.replace(' ', '').split(':') for action in actions]
            models = [model[len(MODEL_DIR):-5] for model in self.models]
            cutmodels = range (0, len(self.models))
            
            
            for i in range(len(actions) - 1, -1, -1):
                if len(actions[i][0]) == 0 or actions[i][0][0] == "#":
                    actions.pop(i)
                    
            for action in actions:
                
                action[0] = action[0].split(',')
                action[1] = action[1].split(',')
                
                for i in range(len(action[0])):                    
                    cutmodels[models.index(action[0][i])] = -1
                
            for i in range(len(cutmodels) - 1, 0, -1):
                if cutmodels[i] > -1:
                    self.models.pop(cutmodels[i])
                    models.pop(cutmodels[i])
                    

            for action in actions:
                
                for i in range(len(action[0])):
                    
                    assert action[0][i] in models, \
                           "<%s> model not found" % action[0][i]
                    
                    action[0][i] = models.index(action[0][i]) + 1
                
                action[1][0] = ACTION_DIR + action[1][0]
                
                dir = glob.glob(ACTION_DIR + '*')
                
                assert action[1][0] in dir, \
                        "<%s> module not found" % action[1][0]
            
            return actions

    def __init__(self, **kwargs):
        """
        Initialize Detectors object. **kwargs is for any __init__ keyword
        arguments to be passed into HotWordDetector __init__() method.
        """

        #####################################
        

        
        threading.Thread.__init__(self)
        self.models = self.load_models()
        self.actions = self.load_actions()
        self.sensitivities = self.load_sensitivities()
        self.init_kwargs = kwargs
        self.interrupted = True
        self.commands = Queue.Queue()
        self.vars_are_changed = True
        self.detectors = None  # Initialize when thread is run in self.run()
        self.run_kwargs = None  # Initialize when detectors start in self.start_recog()
        
        self.change_sensitivity(self.sensitivities)

    def initialize_detectors(self):
        """
        Returns initialized Catpie HotwordDetector objects
        """
        self.detectors = snowboydecoder.HotwordDetector(self.models, self.actions, **self.init_kwargs)
        
        while not self.detectors.hasAudio:
            self.detectors.terminate()
            time.sleep(5)
            self.detectors = snowboydecoder.HotwordDetector(self.models, self.actions, **self.init_kwargs)

    def run(self):
        """
        Runs in separate thread - waits on command to either run detectors
        or terminate thread from commands queue
        """
        try:
            while True:
                command = self.commands.get(True)
                if command == "Start":
                    if self.vars_are_changed or not self.interrupted:
                        # If there is an existing detector object, terminate it
                        if self.detectors is not None:
                            self.detectors.terminate()
                        self.initialize_detectors()
                        self.vars_are_changed = False
                    self.interrupted = False
                    # Start detectors - blocks until interrupted by self.interrupted variable
                    self.detectors.start(interrupt_check=lambda: self.interrupted, **self.run_kwargs)
                    if not self.interrupted:
                        self.commands.put("Start")
                elif command == "Terminate":
                    # Program ending - terminate thread
                    break
        finally:
            if self.detectors is not None:
                self.detectors.terminate()

    def start_recog(self, **kwargs):
        """
        Starts recognition in thread. Accepts kwargs to pass into the
        HotWordDetector.start() method, but does not accept interrupt_callback,
        as that is already set up.
        """
        assert "interrupt_check" not in kwargs, \
            "Cannot set interrupt_check argument. To interrupt detectors, use Detectors.pause_recog() instead"
        self.run_kwargs = kwargs
        self.commands.put("Start")

    def pause_recog(self):
        """
        Halts recognition in thread.
        """
        self.interrupted = True

    def terminate(self):
        """
        Terminates recognition thread - called when program terminates
        """
        
        self.pause_recog()
        self.commands.put("Terminate")

    def is_running(self):
        return not self.interrupted

    def change_models(self, models):
        if self.is_running():
            print("Models will be changed after restarting detectors.")
        if self.models != models:
            self.models = models
            self.vars_are_changed = True

    def change_sensitivity(self, sensitivity):
        if self.is_running():
            print("Sensitivity will be changed after restarting detectors.")
        if self.init_kwargs['sensitivity'] != sensitivity:
            self.init_kwargs['sensitivity'] = sensitivity
            self.vars_are_changed = True


