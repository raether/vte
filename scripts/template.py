#!/usr/bin/python3

import sys
import signal
import os.path
import datetime as dt
import time
import argparse
import textwrap
import logging

from logging.handlers import TimedRotatingFileHandler


#
#  Add other imports here
#

##import socket
##import select
##import json
##import requests
##import subprocess

#
#  Classs Description
#

class VTEClassName:

    #
    #  Initialize File Locations
    #
    mainDirectory    = "/home/camera/vte"
    logDirectory     = mainDirectory + "/logs"
    dataDirectory    = mainDirectory + "/data"
    subDataDirectory = dataDirectory + "/subdata"
    dataFilePrefix   = "data"
    dataFileSuffix   = "csv"
    logFileName      = logDirectory + "/status"

    gpsURL        = "http://control.local:9001"
    radarURL      = "http://control.local:9002"

    waitTime      = 1.0  # Real-time break for main loop
    timeBoundary  = 5    # Minute boundary to roll over information files


    def __init__(self, args):

        logger.debug ("Initializing VTE ClassName Object")


        #
        #  Initialize General Object Parameters
        #
        self.param1      = args.param1
        self.param2      = args.param2
        self.param3      = args.param3

    def VTEfunction(self):

        logger.debug ("Entering VTEFunction")
        logger.info ("Performing Function")
        logger.debug ("Exit VTEFunction")

    def rotateCheck(self):

        currentMinutes = int(dt.datetime.now().minute)

            #   Checks if we are at a multiple of time boundary minutes and if our current minutes don't
            #       equal our last rotation

        if (not(currentMinutes % VTEClassName.timeBoundary)  and  currentMinutes != self.lastRotate):
            logger.debug ("Current Minutes = " + str(currentMinutes))
            logger.debug (vars(self))
            logger.debug ("Check for file rotation.  Rotate File")
            return True

        else:
            return False

    def setDataFile(self):

        logger.debug ("Setting the Data File Name")

        #
        #  Make the video directory if it does not exist
        #

        if not os.path.exists(VTEClassName.subDataDirectory):
            os.makedirs(VTEClassName.subDataDirectory)

        self.dataFile    = VTEClassName.subDataDirectory + '/' + \
                           VTEClassName.dataFilePrefix + "_" + dt.datetime.now().strftime('%Y%m%d_%H%M%S') + \
                             "." + VTEClassName.dataFileSuffix
        self.lastRotate  = int(dt.datetime.now().strftime('%M'))  # Set last rotation

        logger.debug ("Done Setting the Video File Name")

#########################################
#  Main
#########################################
def main(args):

    logger.debug ("Entering main function")

    myObject = VTEClassName(args)        # Create VTE ClassName Object

    try:
        #
        #  Main Loop for Program
        #
        myObject.setDataFile()

        while(True):
            while not (myObject.rotateCheck()):
                logger.info("In Main Loop")
                time.sleep(VTEClassName.waitTime)

            myObject.setDataFile()


    except (KeyboardInterrupt, SystemExit):
        logger.debug("Exiting main function")
        sys.exit(0)

if __name__ == "__main__":

    #
    #  Parse Command Line Options
    #

    
    parser = argparse.ArgumentParser(prog='template.py',
                 formatter_class=argparse.RawDescriptionHelpFormatter,
                 description='Video Taffic Enforcement Template - Version 0.1',
                 epilog=textwrap.dedent('''\
                    Notes
                    -------------------------------------------------------------------------------------------------------
                    Notes go here...
                    -------------------------------------------------------------------------------------------------------
                    '''))

    parser.add_argument('-a', '--param1', default=1920, help="Parameter 1")
    parser.add_argument('-b', '--param2', choices=['value1', 'value2', 'value3'], help="Parameter 2 Values")
    parser.add_argument('-c', '--param3', default='default_value', help="Parameter 3")
    #
    #  Standard Debug Flag
    #
    parser.add_argument('-v', '--debug', action='store_true', help="Turn on debug mode for logging")
#
#  Examples for parsing arguments
#
##    parser.add_argument('-y', '--height', default=1080, help="Set video height <size>. Default 1080")
##    parser.add_argument('-fps', '--framerate', default=30, help="Set video frame rate per second. Default 30") 
##    parser.add_argument('-hf', '--hflip', action='store_true', help="Set Horizontal Flip")
##    parser.add_argument('-vf', '--vflip', action='store_true', help="Set Vertical Flip")
##    parser.add_argument('-q', '--quality', default=25, choices=range(10,40), metavar="[10-40]", help="Video Quality for Encoder (10-40)")
##    parser.add_argument('--vstab', action='store_true', help="Turn on Video Stabilization")
##    parser.add_argument('-exp', '--exposure', default='auto', help="Set exposure mode (see Notes)")
##    parser.add_argument('-awb', '--awb', default='horizon', help="Set AWB mode (see Notes)")
##    parser.add_argument('-d', '--display', choices=['full', 'ul', 'ur', 'lr', 'll'], help="Preview Display (default = Full Screen)")
##    parser.add_argument('-s', '--stream', action='store_true', help="Stream Video to HTTP Port")
##    parser.add_argument('-as', '--annotation', default=50, choices=range(6,160), metavar="[6-160]", help="Text Annotation Size")
##    parser.add_argument('-af', '--foreground', default='white', help="Color for Annotation Text")
##    parser.add_argument('-ab', '--background', default='black', help="Color for Background of Annotation Text")

    args = parser.parse_args()
    
    #
    #  Configure Logging
    #
    FORMAT  = 'ClassName: %(asctime)-15s: %(levelname)-5s: %(message)s'
    logger  = logging.getLogger('status')
    handler = logging.handlers.TimedRotatingFileHandler(VTEClassName.logFileName, when='midnight')
    
    handler.setFormatter(logging.Formatter(FORMAT))

    if (args.debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.addHandler(handler)
                        
    logger.info ("Starting template with parameter 1 = %s", args.param1)
    logger.debug (vars(args))
    
    #
    #  Start main with command-line arguments
    #
    main(args)
