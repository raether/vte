#!/usr/bin/python3

import picamera
import datetime as dt

import sys
import getopt
import signal
import os.path
import argparse
import textwrap
import socket
import select
import time
import json
import requests
import logging

import subprocess

#
#  Video Traffic Enforcement Camera Class
#

class VTECamera:

    #
    #  Initialize File Locations
    #
    mainDirectory = "/home/camera/vte"
    logDirectory  = mainDirectory + "/logs"
    dataDirectory = mainDirectory + "/data"
    logFileName   = logDirectory + "/status"

    gpsURL        = "http://control.local:9001"
    radarURL      = "http://control.local:9002"

    videoDelay       = 1    # Delay before starting camera
    waitTime         = 0.2  # Real-time break during video recording
    fileTimeBoundary = 5    # Minute boundary to roll over video files


    def __init__(self, args):

        logging.debug ("Initializing VTE Camera Object")


        #
        #  Initialize General Object Parameters
        #
        self.cameraView     = str(args.view)
        self.display        = str(args.display)

        if (self.display.lower() == 'ul'):     # Upper Left Display
            self.fullscreen = False
            self.window = (0, 0, 960, 540)

        elif (self.display.lower() == 'ur'):   # Upper Right Display
            self.fullscreen = False
            self.window     = (960, 0, 960, 540)
            
        elif (self.display.lower() == 'll'):   # Lower Left Display
            self.fullscreen = False
            self.window     = (0, 540, 960, 540)

        elif (self.display.lower() == 'lr'):   # Lower Right Display
            self.fullscreen = False
            self.window     = (960, 540, 960, 540)

        else:                                  #  Full Screen Mode
            self.fullscreen = True

        #
        #  Initialize default camera settings
        #  
        self.resHeight      = args.height
        self.resWidth       = args.width
        self.hflip          = args.hflip
        self.vflip          = args.vflip
        self.framerate      = args.framerate
        self.quality        = args.quality
        self.exposure       = args.exposure
        self.awb            = args.awb
        self.videoStabilize = args.vstab
        self.videoFormat    = 'h264'
        
        self.annotationSize = args.annotation
        self.textForeground = args.foreground
        self.textBackground = args.background
        
        #
        #  Initialize Video Streaming
        #
        self.streamVideo  = args.stream

        logging.debug(vars(self))
        logging.debug("Finished initialization")        
    
    #
    #   This class does all of the HTTP Request handling and
    #       provides the object with json data for both gps
    #       and radar information in their respective ports
    #

    def gpsGet(self):
        
        #
        #   HTTP Getter for gps json data
        #
        
        try:
            #   Request data from GPS URL
            r = requests.get(VTECamera.gpsURL, timeout=0.1)
            #   Check status code if success request
            if r.status_code == 200:
                #   Try opening json file we received
                try:
                    self.gpsData = json.loads(r.text)
                    
                except Exception as e:
                    logging.error ("Error Reading JSON File from GPS: %s", e)   
            #   If we got a bad HTTP request        
            else:
                logging.error("Bad GPS HTTP Reqest. Error Code: " + r.status_code)
                
        except Exception as e:
            logging.error ("GPS Exception: %s", e)

    #
    #   This class does all of the gps data handling
    #       as well as formatting for display use
    #

    def gpsAnnotate(self):
        
        #
        #   Sets gps data based on data we received from http request
        #
        #   Here are a list of variables that we assign:
        #       latFloat: Our latitude coordinates
        #       lonFloat: Our longitude coordinates
        #       currentSpeed: Our current speed, read from the car, included as gps data
        #

        #
        #  Send http request to get GPS Data
        #
        self.gpsGet()
        
        try:
        
            self.latFloat     = self.gpsData["Latitude"]
            self.lonFloat     = self.gpsData["Longitude"] #Assign object attributes from parsed data
            self.currentSpeed = self.gpsData["Speed"]

            gpsText        = " Lat: {0:2.6f} ".format(float(self.latFloat)) + \
                             " Long: {0:2.6f} ".format(float(self.lonFloat)) 
        
            vehicleSpeed   = " VS: {0:<3.0f}".format(float(self.currentSpeed))
            
            return (gpsText, vehicleSpeed)
            
        except Exception as e:
            logging.error ("GPS Exception: %s", e)
            gpsText      = "NO GPS DATA"
            vehicleSpeed = " VS: Unknown"
            return (gpsText, vehicleSpeed)
        
    def radarGet(self):
        
        #
        #   HTTP Getter for radar json data
        #
        
        try:
            #   Request data from radar URL
            r = requests.get(VTECamera.radarURL, timeout=0.1)
                #   Check status code if success request
            if r.status_code == 200:
                #   Try opening json file we received
                try: 
                    self.radarData = json.loads(r.text)
                        
                except Exception as e:
                    logging.error ("Error Reading JSON File from Radar: %s", e)    
            else:
                #
                #  Bad HTTP Request
                #
                logging.error("Bad Radar HTTP Reqest. Error Code: " + r.status_code)
                    
        except Exception as e:
            logging.error ("Radar Exception: %s", e)

    def radarAnnotate(self):
    
        #
        #   We combine all of this data into specific formats to be used
        #   The formatted data is placed in the following attributes:
        #       radarText: Formatted radar information based on all atributes in setRadar
        #
        
        self.radarGet() #Call getter function to load radar information
        try:
        
            self.patrolSpeed  = str(self.radarData["PatrolSpeed"]) 
            self.lockedTarget = str(self.radarData["LockedTargetSpeed"])
            self.targetSpeed  = str(self.radarData["TargetSpeed"])
            self.Antenna      = str(self.radarData["Mode"]["antenna"])
            self.Transmit     = str(self.radarData["Mode"]["transmit"])
            self.Direction    = str(self.radarData["Mode"]["direction"])
        
            radarText = " T: " + self.targetSpeed +  "  " + \
                        " L: " + self.lockedTarget + "  " + \
                        " P: " + self.patrolSpeed +  "  " + \
                         self.Direction

            return(radarText)

        except Exception as e:
            logging.error ("Radar Exception: %s", e)
            return("NO RADAR DATA")

    def annotateVideo(self):

        currentTime = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        gpsText, vehicleSpeed = self.gpsAnnotate()
        radarText             = self.radarAnnotate()
        
        cameraAnnotate = "  " + self.cameraView.title() + "  " + \
                              currentTime + "  " + \
                              gpsText + "\n" + \
                              radarText + \
                              vehicleSpeed

        #
        #  Annotate Video
        #
        self.camera.annotate_text = cameraAnnotate
        
    
    def rotateCheck(self):
        
        self.currentMinutes = int(dt.datetime.now().minute)
        
            #   Checks if we are at a multiple of 15 minutes and if our current minutes don't
            #       equal our last rotation
            #   Make sure self.currentMinutes is an int
            
        if(not(self.currentMinutes % VTECamera.fileTimeBoundary)  and  self.currentMinutes != self.lastRotate):
            logging.debug (vars(self))
            logging.debug ("Check for file rotation.  Rotate File")
            return True
        
        else:
            return False

        
    def setVideoFile(self):

        logging.debug ("Setting the Video File Name")

        #
        #  Make the video directory if it does not exist
        #
        self.videoDirectory = self.dataDirectory + '/' + self.cameraView.lower() + '/'
        if not os.path.exists(self.videoDirectory):
            os.makedirs(self.videoDirectory)
    
        self.videoFile      = self.videoDirectory + self.cameraView + "_" + dt.datetime.now().strftime('%Y%m%d_%H%M%S.h264')
        self.lastRotate     = int(dt.datetime.now().strftime('%M'))  #Set last rotation
        

        logging.debug ("Done Setting the Video File Name")
    



    #This class handles all functions from the original PiCamera class, like displaying and running
        
    def outputDisplay(self):

        logging.debug ("Video Output to Display")

        #
        #  Display Video Preview on Screen
        #
        if (self.fullscreen):
            self.camera.start_preview(fullscreen = self.fullscreen)
        else:
            self.camera.start_preview(fullscreen = self.fullscreen, window = self.window)

        logging.debug ("Done Video Output to Display")

    def startCamera(self):

        logging.debug ("Starting camera")
        
        try:
            self.camera = picamera.PiCamera()
        except picamera.PiCameraError:
            logging.critical ("Cannot connect to camera")
            exit(1)

        logging.info ("Camera Board Initialized")
        #
        #  Initialize variables for camera object
        #
        self.camera.resolution          = (self.resWidth, self.resHeight)
        self.camera.framerate           = self.framerate
        self.camera.vflip               = self.vflip
        self.camera.hflip               = self.hflip
        self.camera.annotate_text_size  = self.annotationSize
        self.camera.annotate_foreground = picamera.Color(self.textForeground)
        self.camera.annotate_background = picamera.Color(self.textBackground)
        self.camera.awb_mode            = self.awb

        logging.debug ("Done starting camera")

    def splitCamera(self):

        logging.debug ("Split camera")

        #
        #  Start Recording Video to a File
        #
        self.camera.split_recording(self.videoFile)
        logging.info ("Started recording " + self.videoFile)

        #
        #  Stream Video to a http port
        #
        if(self.streamVideo):
            self.camera.split_recording(self.myvlc.stdin, splitter_port=2)
            logging.info ("Start Streaming Video to HTTP Port")

        logging.debug ("Done split camera")

    def runCamera(self):

        logging.debug ("Running camera")

        #
        #  Start Recording Video to a File
        #
        self.camera.start_recording(self.videoFile, quality = self.quality, format = self.videoFormat)
        logging.info ("Started recording " + self.videoFile)

        #
        #  Stream Video to a http port
        #
        if(self.streamVideo):
            logging.info ("Start Streaming Video to HTTP Port")
            
            cmdline = ['cvlc','-q','stream:///dev/stdin','--sout','#standard{access=http,mux=ts,dst=:5001}',':demux=h264','-' ]
            self.myvlc = subprocess.Popen(cmdline, stdin=subprocess.PIPE)
            self.camera.start_recording(self.myvlc.stdin, format='h264', splitter_port=2, resize=(384, 216))

        logging.debug ("Done running camera")

    def stopCamera(self):

        logging.debug ("Stop camera")

        #
        #  Start Recording Video to a File
        #
        self.camera.stop_recording()
        logging.info ("Stopping video recording")
        logging.info ("Stopping Camera")

        #
        #  Stream Video to a http port
        #
        if(self.streamVideo):
            self.camera.stop_recording(splitter_port=2)
            logging.info ("Stopping video streaming")

        logging.debug ("Done stop camera")

#########################################
#  Main
#########################################
def main(args):

#
#  Basic steps for running the camera.
#
#   1.  Declare the camera object and set properties
#   2.  Configure Camera
#   3.  Check display and preview accordingly
#   4.  Start recording to a file.
#   5.  Send video to stream.
#   6.  Annotate video with timestamp, radar speed info, and GPS info
#   7.  Roll over files on time increment (example:  every 15 minutes)
#

    logging.debug ("Entering main function")

    camera = VTECamera(args)        # Create VTE Camera Object

    time.sleep(VTECamera.videoDelay)

    try:
        camera.startCamera()
        camera.outputDisplay()
        camera.setVideoFile()
        camera.runCamera()

        while(True):    
            while not (camera.rotateCheck()):
                camera.annotateVideo()
                camera.camera.wait_recording(VTECamera.waitTime)
                    
            camera.setVideoFile()
            camera.splitCamera()

    #
    #  Graceful shutdown of camera
    #
    except (KeyboardInterrupt, SystemExit):
        logging.debug("Exiting main function")
        camera.stopCamera()
        sys.exit(0)

if __name__ == "__main__":

    #
    #  Parse Command Line Options
    #

    
    parser = argparse.ArgumentParser(prog='camera.py',
                 formatter_class=argparse.RawDescriptionHelpFormatter,
                 description='Video Taffic Enforcement Camera - Version 0.1',
                 epilog=textwrap.dedent('''\
                    Notes
                    -------------------------------------------------------------------------------------------------------
                    Exposure mode options :
                    off,auto,night,nightpreview,backlight,spotlight,sports,snow,beach,verylong,fixedfps,antishake,fireworks

                    AWB mode options :"
                    off,auto,sunlight,cloudy,shade,tungsten,fluorescent,incandescent,flash,horizon
                    -------------------------------------------------------------------------------------------------------
                    '''))
    
    parser.add_argument('view', choices=['front', 'left', 'rear'], help="Camera View")
    parser.add_argument('-v', '--debug', action='store_true', help="Turn on debug mode for logging")
    parser.add_argument('-x', '--width', default=1920, help="Set video width <size>. Default 1920")
    parser.add_argument('-y', '--height', default=1080, help="Set video height <size>. Default 1080")
    parser.add_argument('-fps', '--framerate', default=30, help="Set video frame rate per second. Default 30") 
    parser.add_argument('-hf', '--hflip', action='store_true', help="Set Horizontal Flip")
    parser.add_argument('-vf', '--vflip', action='store_true', help="Set Vertical Flip")
    parser.add_argument('-q', '--quality', default=25, choices=range(10,40), metavar="[10-40]", help="Video Quality for Encoder (10-40)")
    parser.add_argument('--vstab', action='store_true', help="Turn on Video Stabilization")
    parser.add_argument('-exp', '--exposure', default='auto', help="Set exposure mode (see Notes)")
    parser.add_argument('-awb', '--awb', default='horizon', help="Set AWB mode (see Notes)")
    parser.add_argument('-d', '--display', choices=['full', 'ul', 'ur', 'lr', 'll'], help="Preview Display (default = Full Screen)")
    parser.add_argument('-s', '--stream', action='store_true', help="Stream Video to HTTP Port")
    parser.add_argument('-as', '--annotation', default=50, choices=range(6,160), metavar="[6-160]", help="Text Annotation Size")
    parser.add_argument('-af', '--foreground', default='white', help="Color for Annotation Text")
    parser.add_argument('-ab', '--background', default='black', help="Color for Background of Annotation Text")

    args = parser.parse_args()
    
    #
    #  Configure Logging
    #
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.ERROR)
    if (args.debug):
        logging.basicConfig(filename=VTECamera.logFileName,
                            format='Camera: %(asctime)-15s: %(levelname)-5s: %(message)s',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(filename=VTECamera.logFileName,
                            format='Camera: %(asctime)-15s: %(levelname)-5s: %(message)s',
                            level=logging.INFO)        
                        
    logging.info ("Starting %s camera", args.view)
    logging.debug (vars(args))
    
    #
    #  Start main with command-line arguments
    #
    main(args)
