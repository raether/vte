#!/usr/bin/python

import serial
import io
import threading
import time
import json
from datetime import datetime
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

PORT_NUMBER = 8080
RADAR_DEVICE = "/dev/ttyUSB0"
MESSAGE_LENGTH = 23

#This class will handles any incoming request from
#the browser 
class radarHandler(BaseHTTPRequestHandler):
	
	#Handler for the GET requests
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		# Send the html message
		message = json.dumps({
                        'TargetSpeed' : target_speed,
                        'PatrolSpeed' : patrol_speed,
                        'LockedTarget' : locked_target
                        })
		self.wfile.write(message)
		return

	
        def log_message(self, format, *args):
                return

#################################################################################
#  Main
#################################################################################

        
radar = serial.Serial(port=RADAR_DEVICE, timeout=1)

if radar.isOpen():
   print("Connected to: " + radar.portstr)

#
#  Start up simple HTTP Server to handle requests for radar information
#
server = HTTPServer(('', PORT_NUMBER), radarHandler)

t=threading.Thread(target=server.serve_forever)
t.daemon = True
t.start()

print 'Started httpserver on port ' , PORT_NUMBER
print "Reading Serial Port..."

#
#  Read bytes off of serial port
#
while True:
   try:

        current_byte = radar.read()
        if not current_byte:
                byte_value = 0
                print "Radar Not Connected... Trying to reconnect"
                time.sleep(1)
                radar.close()
                radar = serial.Serial(port=RADAR_DEVICE, timeout=1)
                if radar.isOpen():
                   print("Reconnected to: " + radar.portstr)
        else:
                byte_value = int(current_byte.encode('hex'), 16)
                
        #
        #  Start of Message
        #  Looks for a byte with the theoretical message length of 23.  This seems like a bad way to 
        #  detect the start of a message, but it is the only method available.
        #
        if (byte_value == MESSAGE_LENGTH):

          current_timestamp = datetime.now().strftime('%Y-%m-%d %H;%M:%S')

          for i in range(MESSAGE_LENGTH-1):
             current_byte = radar.read()
             byte_value = int(current_byte.encode('hex'), 16)
             if (i == 0):
                programmable_options = byte_value
             if (i == 1):
                errors = byte_value
             if (i == 2):
                target_speed = byte_value
             if (i == 3):
                patrol_speed = byte_value
             if (i == 4):
                locked_target = byte_value
             if (i == 5):
                mode = byte_value

#
#  Handle exit with ctrl+c
#
        
   except(KeyboardInterrupt, SystemExit): 
      print "Stopping Radar"
      radar.close()
      server.socket.close()
      exit()


