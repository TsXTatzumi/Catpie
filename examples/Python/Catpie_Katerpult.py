import bluetooth
import subprocess
import re
import time
import os
import logging
import RPi.GPIO as GPIO



TOP_DIR = os.path.dirname(os.path.abspath(__file__))

RES_DIR = os.path.join(TOP_DIR, 'resources/')



def connect(mac, newDevice=False):
    process = subprocess.Popen(["bluetoothctl"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    if newDevice:
        logger.info("bluetooth: new device - " + mac)
        process.stdin.write("trust " + mac + "\n")        
        process.stdin.write("pair " + mac + "\n")
        time.sleep(1)
    else:
        logger.info("bluetooth: connect - " + mac)
        
    process.stdin.write("connect " + mac + "\n")
    time.sleep(1)
    
    output, err = process.communicate("quit")
    
    if re.search("Failed to connect:", output) == None:
        logger.info("success")
        return True
    
    logger.info("failed")
    return False


logging.basicConfig()
logger = logging.getLogger("Catpiectl")
logger.setLevel(logging.INFO)

with open(RES_DIR + 'Catpie.cfg') as ConfigFile:
    turnIndicator = re.search("(?<=BlingHelmet 60\t).*", ConfigFile.read())
    
    assert turnIndicator != None, \
        "turn indicator not specified" 
    
    turnIndicator = turnIndicator.group(0)
    
GPIO.setmode(GPIO.BCM)

GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
logger.info("ready...")

while True:
    GPIO.wait_for_edge(3, GPIO.FALLING)
    startPress = time.time()
    logger.info("button press detected!")
    
    while(not GPIO.input(3)):
        time.sleep(0.1)
        
    logger.info("released after " + str(round(time.time() - startPress, 1)) + " seconds")

    if (time.time() - startPress) < 5:
        logger.info("bluetooth setup")
        output = subprocess.check_output("echo \"paired-devices\nquit\" | bluetoothctl", shell = True)
        paired = re.findall("(?<=\nDevice )..:..:..:..:..:..", output)
        
        isConnected = False
        for i in range(len(paired) - 1, -1, -1):
            output = subprocess.check_output("echo \"info " + paired[i] + "\nquit\" | bluetoothctl", shell = True)
            
            if re.search("(?<=Class: ).*", output) == None:
                paired.pop(i)
                continue
            
            devClass = format(int(re.search("(?<=Class: ).*", output).group(0), 16), '0>24b')
            
            if(devClass[2] == '0' or devClass[4] == '0'):
                paired.pop(i)
                continue
            
            if re.search("(?<=Connected: ).*", output).group(0) == "yes":
                isConnected = connect(paired[i])
                
        logger.info(str(len(paired)) + " paired - any connections? " + str(isConnected))
        
        if not isConnected:
            for addr in paired:
                isConnected = connect(addr)
                if isConnected:
                    break
        
        if not isConnected:
            logger.info("scaning for new devices")
            process = subprocess.Popen(["bluetoothctl"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.stdin.write("scan on\n")
            
            time.sleep(10)
            
            output, err = process.communicate(input="scan off\ndevices\nquit")
            
            devices = re.findall("(?<=\nDevice )..:..:..:..:..:..", output)
            
            for addr in devices:
                output = subprocess.check_output("echo \"info " + addr + "\nquit\" | bluetoothctl", shell = True)
                
                if re.search("(?<=Class: ).*", output) == None:
                    continue
                devClass = format(int(re.search("(?<=Class: ).*", output).group(0), 16), '0>24b')
                
                if(devClass[2] == '1' and devClass[4] == '1'):
                    isConnected = connect(addr, newDevice=True)
                    if isConnected:
                        break
        
        connect(turnIndicator)
    else:
        logger.info("shutdown")
        subprocess.call(['shutdown', '-h', 'now'])
