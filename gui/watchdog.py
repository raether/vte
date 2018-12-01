#!/usr/bin/python3

import sys
import signal
import os
import datetime as dt
import time
import argparse
import textwrap
import logging
import threading
import json
import re

from vteControl import VTEControl

from logging.handlers import TimedRotatingFileHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qsl, parse_qs
 
controlData = []
leftData    = []
frontData   = []
rearData    = []

currentTimestamp = ""

leftCameraStatus  = ""
frontCameraStatus = ""
rearCameraStatus  = ""
audioStatus       = ""
radarStatus       = ""
gpsStatus         = ""
gpsLogStatus      = ""
guiStatus         = ""
btStatus          = ""
wifiStatus        = ""

systemButton      = "UNKNOWN"
frontCameraButton = "UNKNOWN"
leftCameraButton  = "UNKNOWN"
rearCameraButton  = "UNKNOWN"
audioButton       = "UNKNOWN"

class watchDogHandler(BaseHTTPRequestHandler):
    
    global controlData, leftData, frontData, rearData, timestamp
    global leftCameraStatus, frontCameraStatus, rearCameraStatus
    global audioStatus, radarStatus, gpsStatus, gpsLogStatus, guiStatus
    global btStatus, wifiStatus
    global systemButton, frontCameraButton, leftCameraButton, rearCameraButton, audioButton
    global buttonStateTime

    #
    #  Function for setting HTTP headers
    #
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
	
    #
    #  HTTP Handler for GET requests
    #
    
    def do_GET(self):

        logger.debug ("HTTP GET Request for WatchDog Data " + self.path)
        
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()

        #
        # Send the response in JSON format
        #

        processList = {}
        processList['leftCamera']  = leftCameraStatus
        processList['frontCamera'] = frontCameraStatus
        processList['rearCamera']  = rearCameraStatus
        processList['audio']       = audioStatus
        processList['radar']       = radarStatus
        processList['GPS']         = gpsStatus
        processList['GPSLogger']   = gpsLogStatus
        processList['GUI']         = guiStatus
        processList['wifi']        = wifiStatus
        processList['bt']          = btStatus
        
        message = json.dumps({'Control'     : controlData,
                              'Left'        : leftData,
                              'Front'       : frontData,
                              'Rear'        : rearData,
                              'ProcessList' : processList,
                              'timestamp'   : timestamp
                              })

        logger.debug (message) 
        self.wfile.write(message.encode('utf-8'))
        
        return
    
    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        global systemButton, frontCameraButton, leftCameraButton, rearCameraButton, audioButton
        global buttonStateTime
        
        logger.debug ("HTTP POST Request for WatchDog Data " + self.path)

        length = int(self.headers.get('Content-Length',0))
        postData = self.rfile.read(length)
        buttonData = json.loads(postData.decode('utf-8'))

        systemButton      = buttonData['system']
        frontCameraButton = buttonData['front']
        leftCameraButton  = buttonData['left']
        rearCameraButton  = buttonData['rear']
        audioButton       = buttonData['audio']

        buttonStateTime = dt.datetime.now()
        logger.debug("Button State Time : " + str(buttonStateTime))
        logger.debug("System Button : " + systemButton)
        logger.debug("Front Camera Button : " + frontCameraButton)
        logger.debug("Left Camera Button : " + leftCameraButton)
        logger.debug("Rear Camera Button : " + leftCameraButton)
        logger.debug("Audio Button : " + audioButton)

        self._set_headers()
        return

    #
    # Absolutely essential!  This ensures that socket resuse is setup BEFORE
    # it is bound.  Will avoid a TIME_WAIT issue
    #
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def log_message(self, format, *args):
        return

class watchDog (threading.Thread):
    
    #
    #  Initialize File Locations
    #
    mainDirectory    = "/home/camera/vte"
    logDirectory     = mainDirectory + "/logs"
    logFileName      = logDirectory + "/status"

    PORT_NUM     = 9003

    watchdogURL   = "http://control.local:9003"

    waitTime      = 10.0  # Real-time break in seconds for main loop
    timeBoundary  = 5     # Minute boundary to roll over information files


 
#########################################
#  Main
#########################################
def main(args):

    global controlData, leftData, frontData, rearData, timestamp
    global leftCameraStatus, frontCameraStatus, rearCameraStatus
    global audioStatus, radarStatus, gpsStatus, gpsLogStatus, guiStatus
    global btStatus, wifiStatus
    global systemButton, frontCameraButton, leftCameraButton, rearCameraButton, audioButton
    global buttonStateTime

    logger.debug ("Entering main function")

    try:

        #
        #  Start up  HTTP Server to handle requests for Watchdog information
        #
        logger.debug("Starting HTTP Server Process")
        server = HTTPServer(('',watchDog.PORT_NUM), watchDogHandler)
        t=threading.Thread(target=server.serve_forever)
        t.daemon = True
        t.start()

        logger.info("Created http server on port " + str(watchDog.PORT_NUM))
        logger.info("Starting to read WatchDog information")

        vte = VTEControl()

        buttonStateTime = dt.datetime.now()

        #
        #  Main Loop for WatchDog
        while True:
            #
            #  Get server telemetry data
            #
            controlData = vte.getServerData("control.local")
            leftData    = vte.getServerData("left.local")
            frontData   = vte.getServerData("front.local")
            rearData    = vte.getServerData("rear.local")
            #
            #  Get status on all the VTE processes and timestamp the status.
            #  Buttons may be pressed on the GUI and the timestamp is used to
            #  determine whether the watchdog status is more up-to-date than
            #  the GUI determiend status.
            #
            
            #
            #  Get the current time
            #
            currentTime = dt.datetime.now()
            timestamp   = currentTime.strftime('%Y-%m-%d %H:%M:%S')
            
            leftCameraStatus  = vte.leftCameraStatus()
            frontCameraStatus = vte.frontCameraStatus()
            rearCameraStatus  = vte.rearCameraStatus()
            audioStatus       = vte.audioStatus()
            radarStatus       = vte.radarStatus()
            gpsStatus         = vte.gpsdStatus()
            gpsLogStatus      = vte.gpsStatus()
            guiStatus         = vte.guiStatus()
            wifiStatus        = vte.wifiStatus()
            btStatus          = vte.btConnected()
            #
            #  Generate time sync report
            #
            vte.genTimeReport()

            elapsedButtonState = (currentTime - buttonStateTime).total_seconds()
            #
            #  Print any debug information
            #
            logger.debug(str(controlData))
            logger.debug(str(leftData))
            logger.debug(str(frontData))
            logger.debug(str(rearData))
            logger.debug("Last Button Status " + str(elapsedButtonState) + " seconds ago")
            logger.debug("System Button is set to : " + systemButton)
            logger.debug("Left Camera Button is set to : " + leftCameraButton)
            #
            #  Wait for configurable pause to do the whole thing again.
            #      A shorter pause will update the status on the GUI more often, but at
            #      the expense of using more CPU cycles.  A longer pause will update the
            #      status on the GUI less often, but will not use as many CPU cycles.
            #
            time.sleep(watchDog.waitTime)

    except (KeyboardInterrupt, SystemExit):
        logger.debug ("Exiting main function")
        logger.debug ("Stopping WatchDog HTTP Server")
        server.shutdown()
        logger.debug ("Closing WatchDog Server Port")
        server.server_close()
        logger.info ("Stopping WatchDog")
        sys.exit(0)

if __name__ == "__main__":

    #
    #  Parse Command Line Options
    #

    
    parser = argparse.ArgumentParser(prog='watchdog.py',
                 formatter_class=argparse.RawDescriptionHelpFormatter,
                 description='Video Taffic Enforcement - Watch Dog - Version 0.1',
                 epilog=textwrap.dedent('''\
                    Notes
                    -------------------------------------------------------------------------------------
                    VTE Watch Dog
                    -------------------------------------------------------------------------------------
                    '''))

    parser.add_argument('-v', '--debug', action='store_true', help="Turn on debug mode for logging")
    args = parser.parse_args()
    
    #
    #  Configure Logging
    #
    FORMAT  = 'WATCHDOG: %(asctime)-15s: %(levelname)-5s: %(message)s'
    logger  = logging.getLogger('status')
    handler = logging.handlers.TimedRotatingFileHandler(watchDog.logFileName, when='midnight')
    
    handler.setFormatter(logging.Formatter(FORMAT))

    if (args.debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.addHandler(handler)
                        
    logger.info ("Starting Watch Dog")
    logger.debug (vars(args))
    
    #
    #  Start main with command-line arguments
    #
    main(args)
