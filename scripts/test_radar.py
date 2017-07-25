
import sys
import signal
import os.path

import socket
import select
import time
import json
import requests

import subprocess


try:
    r = requests.get('http://left.local:9002')
    if r.status_code == 200:
        data = json.loads(r.text)
        patrol_speed  = str(data["PatrolSpeed"])
        locked_target = str(data["LockedTargetSpeed"])
        target_speed  = str(data["TargetSpeed"])
        antenna       = str(data["Mode"]["antenna"])
        transmit      = str(data["Mode"]["transmit"])
        direction     = str(data["Mode"]["direction"])
    else:
        radar_text = "NO RADAR DATA    "
        print radar_text
except:
    radar_text = "NO RADAR DATA    "
    print radar_text

radar_text = " T: " + target_speed +  "  " + \
             " L: " + locked_target + "  " + \
             " P: " + patrol_speed +  "  " + \
             antenna + " " + transmit + " " + direction

print radar_text
