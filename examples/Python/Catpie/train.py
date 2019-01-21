import bluetooth
import subprocess

##nearby_devices = bluetooth.discover_devices(lookup_names=True, flush_cache = True, duration = 5)
##print("found %d devices" % len(nearby_devices))
##
##for addr, name in nearby_devices:
##    print("  %s - %s" % (addr, name))
##    

output = subprocess.check_output("echo \"info 20:74:CF:17:05:AA\nquit\" | bluetoothctl", shell = True)
    ##subprocess.call(["echo", "-e", "\"info 20:74:CF:17:05:AA\nquit\"", "|", "bluetoothctl"])
print output
print("")
