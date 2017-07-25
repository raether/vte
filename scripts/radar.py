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

c_uint8 = ctypes.c_uint8

PORT_NUMBER = 9002
RADAR_DEVICE = "/dev/ttyUSB0"
MESSAGE_LENGTH = 23

main_directory     = "/home/camera/vte"
log_directory      = main_directory + "/logs"
data_directory     = main_directory + "/data"
radarlog_directory = data_directory + "/radar/"
logfile_out        = log_directory + "/status.log"

###############################################################################
# HTTP Server for retrieving Radar Data
###############################################################################
class radarHandler(BaseHTTPRequestHandler):

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
            radarDoc = RadarDoc()
            #
            # Prepare Data into JSON Format
            #
            message = json.dumps(radarDoc.reprJSON(), cls=RadarDataEncoder)
            #
            #  Send the HTML Message
            self.wfile.write(message)
            return
	
    def log_message(self, format, *args):
        return

###############################################################################
#  Class definitions for bit strucutures in radar protocol
###############################################################################

#  Data Sequence 1 - Programmable Options

class ProgrammableOptions_bits( ctypes.LittleEndianStructure ):
    _fields_ = [
                ("metric",        c_uint8, 1 ),  # bit 0
                ("autoUnlock",    c_uint8, 1 ),  # bit 1
                ("harmonic",      c_uint8, 1 ),  # bit 2
                ("ZeroAudio",     c_uint8, 1 ),  # bit 3
                ("empty4",        c_uint8, 1 ),  # bit 4
                ("windowFastest", c_uint8, 1 ),  # bit 5
                ("empty6",        c_uint8, 1 ),  # bit 6
                ("empty7",        c_uint8, 1 ),  # bit 7
               ]
    
class ProgrammableOptions( ctypes.Union ):
    _anonymous_ = ("bit",)
    _fields_ = [
                ("bit",   ProgrammableOptions_bits ),
                ("field", c_uint8    )
               ]

#  Data Sequence 2 = Errors

class Errors_bits( ctypes.LittleEndianStructure ):
    _fields_ = [
                ("rs232InterfaceFault",        c_uint8, 1 ),  # bit 0
                ("radioFrequencyInterference", c_uint8, 1 ),  # bit 1
                ("noAntennas",                 c_uint8, 1 ),  # bit 2
                ("empty3",                     c_uint8, 1 ),  # bit 3
                ("CrystalCrossCheckFailure",   c_uint8, 1 ),  # bit 4
                ("DSPCommunicationFault",      c_uint8, 1 ),  # bit 5
                ("DSPNotRespnding",            c_uint8, 1 ),  # bit 6
                ("LowVoltage",                 c_uint8, 1 ),  # bit 7
               ]
    
class Errors( ctypes.Union ):
    _anonymous_ = ("bit",)
    _fields_ = [
                ("bit",   Errors_bits ),
                ("field", c_uint8    )
               ]

class ErrorsDoc:
    def __init__(self):

        self.errorList = []
        
        if (errors.rs232InterfaceFault):
            self.errorList = self.errorList + ["rs232InterfaceFault"]
        if (errors.radioFrequencyInterference):
            self.errorList = self.errorList + ["radioFrequencyInterference"]
        if (errors.noAntennas):
            self.errorList = self.errorList + ["noAntennas"]   
        if (errors.CrystalCrossCheckFailure):
            self.errorList = self.errorList + ["CrystalCrossCheckFailure"]
        if (errors.DSPCommunicationFault):
            self.errorList = self.errorList + ["DSPCommunicationFault"]   
        if (errors.DSPNotRespnding):
            self.errorList = self.errorList + ["DSPNotRespnding"]
        if (errors.LowVoltage):
            self.errorList = self.errorList + ["LowVoltage"]   
            
    def reprJSON(self):
        return list(self.errorList) 


#  Data Sequence 6 - Mode

class Mode_bits( ctypes.LittleEndianStructure ):
    _fields_ = [
                ("antenna",   c_uint8, 1 ),  # bit 0
                ("direction", c_uint8, 1 ),  # bit 1
                ("movement",  c_uint8, 1 ),  # bit 2
                ("transmit",  c_uint8, 1 ),  # bit 3
                ("empty4",    c_uint8, 1 ),  # bit 4
                ("empty5",    c_uint8, 1 ),  # bit 5
                ("empty6",    c_uint8, 1 ),  # bit 6
                ("type",      c_uint8, 1 ),  # bit 7
               ]
    
class Mode( ctypes.Union ):
    _anonymous_ = ("bit",)
    _fields_ = [
                ("bit",   Mode_bits ),
                ("field", c_uint8    )
               ]

class ModeDoc:
    def __init__(self):
        
        if (mode.antenna):
            self.antenna = "RearAntenna"
        else:
            self.antenna = "FrontAntenna"

        if (mode.direction):
            self.direction = "SameDirection"
        else:
            self.direction = "OppositeDirection"

        if (mode.movement):
            self.movement = "Moving"
        else:
            self.movement = "Stationary"

        if (mode.transmit):
            self.transmit = "Hold"
        else:
            self.transmit = "Transmit"
            
    def reprJSON(self):
        return dict(antenna = self.antenna, direction = self.direction, movement = self.movement,
                    transmit = self.transmit) 

#  Data Sequence 12 - Antenna Connections

class AntennaConnections_bits( ctypes.LittleEndianStructure ):
    _fields_ = [
                ("rearAntenna",  c_uint8, 2 ),  # bit 0-1
                ("empty2",       c_uint8, 1 ),  # bit 1
                ("empty3",       c_uint8, 1 ),  # bit 2
                ("frontAntenna", c_uint8, 2 ),  # bit 3-4
                ("empty6",       c_uint8, 1 ),  # bit 6
                ("empty7",       c_uint8, 1 ),  # bit 7
               ]
    
class AntennaConnections( ctypes.Union ):
    _anonymous_ = ("bit",)
    _fields_ = [
                ("bit",   AntennaConnections_bits ),
                ("field", c_uint8    )
               ]
class AntennaConnectionsDoc:
    def __init__(self):
        
        if (antennaConnections.rearAntenna == 0):
            self.rearAntenna = "noAntenna"
        elif (antennaConnections.rearAntenna == 1):
            self.rearAntenna = "X-band"
        elif (antennaConnections.rearAntenna == 2):
            self.rearAntenna = "K-band"
        elif (antennaConnections.rearAntenna == 3):
            self.rearAntenna = "Ka-band"

        if (antennaConnections.frontAntenna == 0):
            self.frontAntenna = "noAntenna"
        elif (antennaConnections.frontAntenna == 1):
            self.frontAntenna = "X-band"
        elif (antennaConnections.frontAntenna == 2):
            self.frontAntenna = "K-band"
        elif (antennaConnections.frontAntenna == 3):
            self.frontAntenna = "Ka-band"
            
    def reprJSON(self):
        return OrderedDict([("FrontAntenna", self.frontAntenna),
                            ("RearAntenna", self.rearAntenna)])
    
#
#  General JSON Data Encoders
#

class RadarDoc:
    def __init__(self):
        self.errors = ErrorsDoc()
        self.targetSpeed = targetSpeed
        self.patrolSpeed = patrolSpeed
        self.lockedTargetSpeed = lockedTargetSpeed
        self.mode = ModeDoc()
        self.lockedPatrolSpeed = lockedPatrolSpeed
        self.antennaConnections = AntennaConnectionsDoc()
        
    def reprJSON(self):
        return OrderedDict([("Errors", self.errors),
                            ("TargetSpeed", self.targetSpeed),
                            ("PatrolSpeed", self.patrolSpeed),
                            ("LockedTargetSpeed", lockedTargetSpeed),
                            ("LockedPatrolSpeed", lockedPatrolSpeed),
                            ("Mode", self.mode),
                            ("AntennaConnections", self.antennaConnections)])

class RadarDataEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

#################################################################################
#  Main
#################################################################################
#
#  Initialized Message Structure
#
programmableOptions = ProgrammableOptions()
errors              = Errors()
targetSpeed         = 0
patrolSpeed         = 0
lockedTargetSpeed   = 0
mode                = Mode()
distanceLow         = 0
distanceHigh        = 0
elapsedTimeLow      = 0
elapsedTimeHigh     = 0
lockedPatrolSpeed   = 0
antennaConnections  = AntennaConnections()

#  TODO:
#  RADAR_DEVICE is a hard coded string.   Code should be enhanced to find the
#  USB to serial port convertor PL2303 and set the device
#
   
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

log = open(logfile_out, "a", 1) # non blocking
radarlog = vteLog(radarlog_directory,'radar','csv')

#
#  Read bytes off of serial port
#
while True:
   try:

        current_byte = radar.read()

        #  TODO:  Need to make this more bullet proof for power-on and power-off of radar unit
            
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

          current_timestamp = datetime.now().strftime('%Y-%m-%d %H;%M:%S.%f')[:-3]

          for i in range(1, MESSAGE_LENGTH):
              
            current_byte = radar.read()
            hex_value    = current_byte.encode('hex')
            int_value    = int(hex_value, 16)

            # Data Sequence 1 - Programmable Options
            if (i == 1):
                programmableOptions = int_value

            # Data Sequence 2 - Errors
            if (i == 2):
                errors.field = int_value

            # Data Sequence 3 - Target Speed
            if (i == 3):
                targetSpeed = int_value

            # Data Sequence 4 - Patrol Speed
            if (i == 4):
                patrolSpeed = int_value

            # Data Sequence 5 - Locked Speed
            if (i == 5):
                lockedTargetSpeed = int_value

            # Data Sequence 6 - Mode
            if (i == 6):
                mode.field = int_value

            # Data Sequence 7 - Distance-Low
            if (i == 7):
                distanceLow = int_value

            # Data Sequence 8 = Distance-High
            if (i == 8):
                distanceHigh = int_value

            # Data Sequence 9 - Elapsed-Time-Low
            if (i == 9):
                elapsedTimeLow = int_value

            # Data Sequence 10 - Elapsed-Time-High
            if (i == 10):
                elapsedTimeHigh = int_value

            # Data Sequence 11 - Locked Patrol Speed
            if (i == 11):
                lockedPatrolSpeed = int_value

            # Data Sequence 12 - Antenna Connections
            if (i == 12):
                antennaConnections.field = int_value            

          radarlog.write_log(str(current_timestamp) + ', '+ \
                             str(targetSpeed) + ', ' + \
                             str(patrolSpeed) + ', ' + \
                             str(lockedTargetSpeed) + ', ' + \
                             str(mode) + ', ' + \
                             str(errors) + '\n')

#
#  Handle exit with ctrl+c
#
        
   except(KeyboardInterrupt, SystemExit): 
      print "Stopping Radar"
      radar.close()
      print "Stopping Radar HTTP Server"
      server.shutdown()
      print "Closing HTTP Server Port"
      server.server_close()
      exit()
