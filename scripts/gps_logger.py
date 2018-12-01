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

from logging.handlers import TimedRotatingFileHandler
from gps3.agps3threaded import AGPS3mechanism
from http.server import BaseHTTPRequestHandler, HTTPServer
from vtelog import vteLog

class gpsHandler(BaseHTTPRequestHandler):


	
    #
    #  HTTP Handler for GET requests for GPS Data on the network
    #
    
    def do_GET(self):
        
        global curr_lat
        global curr_long
        global curr_time
        global curr_eps
        global curr_epx
        global curr_epv
        global curr_ept
        global curr_heading
        global curr_speed
        global curr_status

        logger.debug ("HTTP GET Request for GPS Data")
        
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()

        #
        # Send the response in JSON format
        #
        message = json.dumps({
                        'Latitude'  : curr_lat,
                        'Longitude' : curr_long,
                        'Time'      : curr_time,
                        'Speed'     : curr_speed,
                        'Heading'   : curr_heading,
                        'ErrorEps'  : curr_eps,
                        'ErrorEpx'  : curr_epx,
                        'ErrorEpv'  : curr_epv,
                        'ErrorEpt'  : curr_ept
                        })

        logger.debug (message) 
        self.wfile.write(message.encode('utf-8'))
        return

    # Absolutely essential!  This ensures that socket resuse is setup BEFORE
    # it is bound.  Will avoid a TIME_WAIT issue
    #
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def log_message(self, format, *args):
        return

class GpsPoller(threading.Thread):
    
    #
    #  Initialize File Locations
    #
    mainDirectory    = "/home/camera/vte"
    logDirectory     = mainDirectory + "/logs"
    dataDirectory    = mainDirectory + "/data"
    subDataDirectory = dataDirectory + "/gps/"
    dataFilePrefix   = "gps"
    dataFileSuffix   = "csv"
    logFileName      = logDirectory + "/status"

    GPS_PORT_NUM     = 9001

    gpsURL        = "http://control.local:9001"
    radarURL      = "http://control.local:9002"

    waitTime      = 1.0  # Real-time break for main loop
    timeBoundary  = 5    # Minute boundary to roll over information files


 
#########################################
#  Main
#########################################
def main(args):

    global curr_lat
    global curr_long
    global curr_time
    global curr_eps
    global curr_epx
    global curr_epv
    global curr_ept
    global curr_heading
    global curr_speed
    global curr_status

    logger.debug ("Entering main function")
    logger.debug ("Log at " + GpsPoller.subDataDirectory)
    
    gpslog = vteLog (GpsPoller.subDataDirectory, GpsPoller.dataFilePrefix, \
                    GpsPoller.dataFileSuffix, GpsPoller.timeBoundary)

    gpsd = AGPS3mechanism()

    try:

        #
        #  Create the GPS Poller Thread
        #
        logger.debug("Creating GPS Poller Process")

        gpsd.stream_data()
        gpsd.run_thread() 

        #
        #  Start up simple HTTP Server to handle requests for GPS information
        #
        logger.debug("Starting HTTP Server Process")
        server = HTTPServer(('',GpsPoller.GPS_PORT_NUM), gpsHandler)
        t=threading.Thread(target=server.serve_forever)
        t.daemon = True
        t.start()

        logger.info("Created http server on port " + str(GpsPoller.GPS_PORT_NUM))
        logger.info("Starting to read GPS information")

        while True:
            #
            #  Main Loop for Program
            #

            curr_lat     = gpsd.data_stream.lat
            curr_long    = gpsd.data_stream.lon
            curr_time    = gpsd.data_stream.time
            curr_eps     = gpsd.data_stream.eps
            curr_epx     = gpsd.data_stream.epx
            curr_epv     = gpsd.data_stream.epv
            curr_ept     = gpsd.data_stream.ept
            curr_heading = gpsd.data_stream.track

            if (gpsd.data_stream.speed == 'n/a'):
                curr_speed = 0.0
            else:
                curr_speed = round(float(gpsd.data_stream.speed) * 2.23694)

            current_timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            gpslog.writeLog (str(current_timestamp) + ', ' + \
                             str(curr_time) + ', ' + \
                             str(curr_lat) + ', ' + \
                             str(curr_long) + ', ' + \
                             str(curr_speed) + ', ' + \
                             str(curr_heading) + ', ' + \
                             str(curr_eps) + ', ' + \
                             str(curr_epx) + ', ' + \
                             str(curr_epv) + ', ' + \
                             str(curr_ept) + '\n')
            

            time.sleep(GpsPoller.waitTime)

    except (KeyboardInterrupt, SystemExit):
        logger.debug ("Exiting main function")
        logger.debug ("Stopping Radar HTTP Server")
        server.shutdown()
        logger.debug ("Closing HTTP Server Port")
        server.server_close()
        logger.info ("Stopping GPS Poller")
        sys.exit(0)

if __name__ == "__main__":

    #
    #  Parse Command Line Options
    #

    
    parser = argparse.ArgumentParser(prog='gps_logger.py',
                 formatter_class=argparse.RawDescriptionHelpFormatter,
                 description='Video Taffic Enforcement GPS Logger - Version 0.1',
                 epilog=textwrap.dedent('''\
                    Notes
                    -------------------------------------------------------------------------------------------------------
                    GPS Logger
                    -------------------------------------------------------------------------------------------------------
                    '''))

    parser.add_argument('-v', '--debug', action='store_true', help="Turn on debug mode for logging")
    args = parser.parse_args()
    
    #
    #  Configure Logging
    #
    FORMAT  = 'GPS: %(asctime)-15s: %(levelname)-5s: %(message)s'
    logger  = logging.getLogger('status')
    handler = logging.handlers.TimedRotatingFileHandler(GpsPoller.logFileName, when='midnight')
    
    handler.setFormatter(logging.Formatter(FORMAT))

    if (args.debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.addHandler(handler)
                        
    logger.info ("Starting GPS Logger")
    logger.debug (vars(args))
    
    #
    #  Start main with command-line arguments
    #
    main(args)
