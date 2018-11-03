#!/usr/bin/python

import serial
import io
import threading
import time
import json
import ctypes
import struct

from datetime import datetime
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from vtelog import vteLog
from collections import OrderedDict
from subprocess import PIPE, Popen

c_uint8 = ctypes.c_uint8

PORT_NUMBER = 9003
CONTROLLER_DEVICE = "/dev/arduino"

main_directory     = "/home/camera/vte"
log_directory      = main_directory + "/logs/"
data_directory     = main_directory + "/data"
logfile_out        = log_directory + "/status"

###############################################################################
# HTTP Server for retrieving Radar Data
###############################################################################
class environmentHandler(BaseHTTPRequestHandler):

    #	
    # Handler for the GET requests
    #
    def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            #
            #  Initialized JSON Structure for Data
            #
            environmentDoc = EnvironmentDoc()
            #
            # Prepare Data into JSON Format
            #
            message = json.dumps(environmentDoc.reprJSON(), cls=EnvironmentDataEncoder)
            #
            #  Send the HTML Message
            self.wfile.write(message)
            return
	
    def log_message(self, format, *args):
        return
    
#
#  General JSON Data Encoders
#

class EnvironmentDoc:
    def __init__(self):
        self.left_cpu_temp = left_cpu_temp
        self.front_cpu_temp = front_cpu_temp
        self.rear_cpu_temp = rear_cpu_temp
        self.fanSpeed = fanSpeed
        
    def reprJSON(self):
        return OrderedDict([("LeftCPUTemp", self.left_cpu_temp),
                            ("FrontCPUTemp", self.front_cpu_temp),
                            ("RearCPUTemp", self.rear_cpu_temp),
                            ("FanSpeed", self.fanSpeed)])

class EnvironmentDataEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

def get_local_cpu_temperature():
#    """get cpu temperature using vcgencmd"""
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])

def get_remote_cpu_temperature(hostname):
#    """get cpu temperature using vcgencmd"""
    process = Popen(['ssh', hostname, 'vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])

#################################################################################
#  Main
#################################################################################

#
#  Start up simple HTTP Server to handle requests for radar information
#

server = HTTPServer(('', PORT_NUMBER), environmentHandler)

t=threading.Thread(target=server.serve_forever)
t.daemon = True
t.start()

print 'Started httpserver on port ' , PORT_NUMBER

log = open(logfile_out, "a", 1) # non blocking
environmentlog = vteLog(log_directory,'environment','csv')

while True:
    try:   
        controller = serial.Serial(port=CONTROLLER_DEVICE, baudrate=9600, writeTimeout=1)

        if controller.isOpen():
           print("Connected to: " + controller.portstr)

        #
        #  Write fan speed on serial port
        #
        while True:
            try:

                #
                #  Get temperatures of CPUs and GPUs
                #
                left_cpu_temp = get_local_cpu_temperature()
                front_cpu_temp = get_remote_cpu_temperature('front.local')
                rear_cpu_temp = get_remote_cpu_temperature('rear.local')
                max_cpu_temp = max(left_cpu_temp, front_cpu_temp, rear_cpu_temp)

                #
                #  Computer fan speed based on temperature
                #
                if max_cpu_temp > 70:
                    fanSpeed = 255   # full-speed
                elif max_cpu_temp > 60:
                    fanSpeed = 225   # high
                elif max_cpu_temp > 50:
                    fanSpeed = 200   # medium-high
                elif max_cpu_temp > 40:
                    fanSpeed = 150   # medium
                else:
                    fanSpeed = 0

                #
                #  Write fan speed value from 0-255
                #
                controller.write(chr(fanSpeed))

                #
                #  Write information to log file
                #
                current_timestamp = datetime.now().strftime('%Y-%m-%d %H;%M:%S.%f')[:-3]
                environmentlog.write_log(str(current_timestamp) + ', ' + \
                                         str(left_cpu_temp)     + ', ' + \
                                         str(front_cpu_temp)    + ', ' + \
                                         str(rear_cpu_temp)     + ', ' + \
                                         str(fanSpeed) + '\n')

                time.sleep(10)
            #
            #  Exception for not being able to write to serial port.
            #  Close down connection and re-establish connection
            #
            except(serial.SerialException):
                print "Serial Exception - Stopping Controller Interface"
                if controller.isOpen():
                    controller.close()
                time.sleep(10)
                
                print "Trying to Reconnect to Controller Interface"
                controller = serial.Serial(port=CONTROLLER_DEVICE, baudrate=9600, writeTimeout=1)
                if controller.isOpen():
                   print("Connected to: " + controller.portstr)
                
    except(serial.SerialException):
        print "Serial Exception - Cannot Connect to Controller Interface"
        time.sleep(10)

#
#  Handle exit with ctrl+c
#
    except(KeyboardInterrupt, SystemExit): 
        print "Stopping Controller Interface"
        controller.close()
        print "Stopping Controller HTTP Server"
        server.shutdown()
        print "Closing HTTP Server Port"
        server.server_close()
        exit()
