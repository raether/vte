#!/usr/bin/python3
#

from __future__ import print_function
from datetime import datetime, timedelta, timezone
import datetime
import picamera
from PIL import Image
from picamera import Color
from picamera import PiCamera
import datetime as dt
import sys
import getopt
import signal
import os.path
import argparse
import socket
import select
import time
import json
import requests
import subprocess

class VTECamera(PiCamera, GPS, Radar, FileManager, Property):
    #Subclass which inherits properties from the PiCamera library, and other subclasses
    #This class will do all of the FINAL work, like calling all methods and running camera functions

    def __init__(self):

        #Give it all of the objects

        self.camera          = PiCamera()
        self.gps             = GPS()
        self.radar           = Radar()
        self.file_manager    = FileManager()
        self.property        = Property()
        
    def initCamera(self):

        self.openThread()

        self.camera.resolution          = (self.property.Width, self.property.Height)

        self.camera.framerate           = self.property.cameraFramerate
        
        self.camera.vflip               = self.property.setVFlip
        
        self.camera.hflip               = self.property.setHFlip
        
        self.camera.annotate_text_size  = self.property.annotateSize
        
        self.camera.annotate_foreground = Color(self.property.cameraColor.title())
        
        self.camera.awb_mode            = self.property.cameraAwb

    def loopCamera(self):

        self.file_manager.writeFile()

        self.outputDisplay()

        self.camera.start_recording(self.file_manager.videoFile, self.property.Quality, self.property.Format)

        if(self.property.streamVideo): 
        self.camera.start_recording(self.property.Vlc.stdin, self.property.Format, self.property.splitterPort)
            
        while not(self.file_manager.rotateCheck()):
                            self.doAnnotate()
                            self.waitRecording()

        if(self.property.streamVideo):
                self.stopRecording()

        sys.exit(0)

    def outputDisplay(self):

        self.property.setDisplay()

        if (not(self.property.Window)):
            self.camera.start_preview(self.property.Fullscreen)
        else:
            self.camera.start_preview(self.property.Fullscreen, self.property.Window)

    def doAnnotate(self):

        self.Property.setAnnotate()

        self.camera.annotate_text = self.property.cameraAnnotate

    def openThread(self):

        self.property.setClvc()

        if(self.streamVideo): 
            self.property.Vlc = subprocess.Popen(self.property.cmdLine, stdin = subprocess.PIPE) #Opens subprocess for clvc streaming

    def waitRecording(self):

        #Recommended for timeout 

        self.camera.wait_recording(self.property.timeoutSeconds)

    def stopRecording(self):

        #Stops recording if we are streaming video

        if(self.streamVideo):
            self.camera.stop_recording(self.property.timeoutSeconds)

class GPS(): 
    #This class will handle all of the GPS Data, including HTTP GETs, Formatting, and Writing

    def __init__(self):

        #Default values for object attributes

        self.gpsText      = " NO GPS DATA "
        self.vehicleSpeed = " NO SPEED DATA "
        self.latFloat     = None
        self.lonFloat     = None
        self.gpsData      = None
        self.gpsError     = None

    def getGps(self):

        #Gets json structure through http

        try:
            
            r = requests.get('http://left.local:9001')
            
            if r.status_code == 200:
                
                try:
                    self.gpsData = json.loads(r.text)
                    
                except Exception as e:
                    print (e)
                    self.gpsError = e
            
            else:
                self.gpsError = "Bad HTTP Reqest. Error Code: " + r.status_code
                
        except Exception as e:
            print (e)
            self.gpsError = e

    def setGps(self):

        #Sets gps information into object attributes

        self.getGps()

        try:
        
            self.latFloat     = self.gpsData["Latitude"]
            self.lonFloat     = self.gpsData["Longitude"] 
            self.currentSpeed = self.gpsData["Speed"]
            
        except Exception as e:             print(e)
            self.gpsError     = e

    def formatGps(self):

        #Formats gps text for display

        self.setGps()

        try:
        
            self.gpsText      = " Lat: {0:2.6f} ".format(float(self.latFloat)) + \
            " Long: {0:2.6f} ".format(float(self.lonFloat)) 
        
            self.vehicleSpeed = " VS: {0:<3.0f}".format(float(self.currentSpeed))

        except Exception as e:
            print(e)
            self.gpsError     = e


class Radar(): 
    #This class will handle all of the Radar Data, including HTTP GETs, Formatting, and Writing

    def __init__(self):

        #Default values for object attributes

        self.radarText   = " NO RADAR DATA "
        self.radarData   = None
        self.targetSpeed = None
        self.radarError  = None

    def getRadar(self):

        #Gets json structure through http

        try:
          
            r = requests.get('http://left.local:9002')
               
            if r.status_code == 200:
                    
                try: 
                    self.radarData = json.loads(r.text)
                        
                except Exception as e:
                    print (e)
                    self.radarError = e
    
            else:
                self.radarError = "Bad HTTP Reqest. Error Code: " + r.status_code
                    
        except Exception as e:
            print (e)
            self.radarError = e

    def setRadar(self):

        #Sets radar information into object attributes

        self.getRadar()

        try:
        
            self.patrolSpeed  = str(self.radarData["PatrolSpeed"]) 
            self.lockedTarget = str(self.radarData["LockedTargetSpeed"]) 
            self.targetSpeed  = str(self.radarData["TargetSpeed"])
            self.Antenna      = str(self.radarData["Mode"]["antenna"])
            self.Transmit     = str(self.radarData["Mode"]["transmit"])
            self.Direction    = str(self.radarData["Mode"]["direction"])
            
        except Exception as e:
            print(e)
            self.radarError   = e

    def formatRadar(self):

        #Formats radar text for display

        self.setRadar()

        try:
        
            self.radarText = " T: " + self.targetSpeed +  "  " + \
            " L: " + self.lockedTarget + "  " + \
            " P: " + self.patrolSpeed +  "  " + \
            self.Direction

        except Exception as e:
            print(e)
            self.radarError  = e

class FileManager(): 
    #This class will handle all file management, including writing to logs

    def __init__(self):

        #Default values for object attributes

        self.currentMinutes = datetime.datetime.now().minute
        self.lastRotate     = self.currentMinutes
        self.currentTime    = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.mainDirectory  = "/home/camera/vte"
        self.logDirectory   = self.mainDirectory + "/logs"
        self.dataDirectory  = self.mainDirectory + "/data"
        self.logFileOut     = self.logDirectory + "/status.log"

    def rotateCheck(self):

        #Checks if we are ready to rotate a new log file

        self.currentMinutes = datetime.datetime.now().minute
            
        if(not(self.currentMinutes % 15)  and  self.currentMinutes != self.lastRotate):
            print ("Done checking for rotation.")
            return True
        
        else:
            print ("Done checking for rotation.")
            return False

    def writeFile(self):

        #Writes log file

        self.videoDirectory = self.dataDirectory + '/' + self.cameraView.lower() + '/' 
    
        self.videoFile      = self.videoDirectory + self.cameraView + "_" + dt.datetime.now().strftime('%Y%m%d_%H%M.h264')
        
        self.lastRotate     = dt.datetime.now().strftime('%M') 
        
        self.logData        = dt.datetime.now().strftime('%T [CAMERA]: ') + "Started recording " + self.videoFile + "\n"
        
        self.log.write(self.logData) 


class Property(GPS, Radar): 
    #This class will handle all display options, including setting display properties, positioning, and text annotation
    #As well as camera properties and input
    
    def __init__(self):

        #Give objects

        self.gps = GPS()
        self.radar = Radar()

        #Default values for object attributes

        self.Display         = 'full'    #Key: ul=upper left, ur=upper right, ll=lower left, lr=lower right
        self.setVFlip        = False     #If true, flips over y-axis
        self.setHFlip        = False     #If true, flips over x-axis
        self.splitterPort    = 2         #Port from splitter
        self.Vlc             = None      #VLC manager
        self.Width           = 1920      #Width of window
        self.Height          = 1080      #Height of window
        self.cameraView      = 'left'    #Which camera we view
        self.annotateSize    = 17        #Size of text overlay 
        self.textColor       = 'white'   #Color of text overlay
        self.Window          = None      #Coordinates of preview window
        self.Format          = 'h264'    #Video format
        self.streamVideo     = False     #If true, video streams to port
        self.textBackground  = None      #Background for text overlay
        self.cameraFramerate = 24        #Framerate of camera, 
        self.propertyArgs    = None      #Property args from command line
        self.cameraAwb       = 'horizon' #Auto white balance, default is horizon for some reason
        self.Quality         = 25        #Quality of recording
        self.cameraAnnotate  = ""

    def propertyInput(self):

        #Command line input method for camera properties

        try:
            opts, args = getopt.getopt(self.args, "hmd:sv:a:b:w:l:f:q:xyc:z:o:p:", ["help","man", "display=", "stream", "view=", "annsize=", "background=", "width=", "height=", "framerate=", "quality=", "vflip", "hflip", "color=", "awb=", "format=", "splitter="])
        except getopt.GetoptError:
            print ('camera.py -h <help*> -d <display> -s <stream*> -v <view> -a <annsize>\n-b <background> -w <width> -l <height> -f <framerate> -q <quality>\n-x <vflip*> -y <hflip*> -c <color> -z <awb> -o <format>\n-p <splitter>\n\n*=flag only')
            sys.exit(2) 
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print('camera.py -h <help*> -d <display> -s <stream*> -v <view> -a <annsize>\n-b <background> -w <width> -l <height> -f <framerate> -q <quality>\n-x <vflip*> -y <hflip*> -c <color> -z <awb> -o <format>\n-p <splitter>\n\n*=flag only')
                                      
                sys.exit()
            elif opt in ("-m", "--man":
                print("Welcome to the very lazy manpage: #Default values for object attributes\nself.Display         = 'full'    #Key: ul=upper left, ur=upper right, ll=lower left, lr=lower right\nself.setVFlip        = False     #If true, flips over y-axis\nself.setHFlip        = False     #If true, flips over x-axis\nself.splitterPort    = 2         #Port from splitter\nself.myVlc           = None      #VLC manager\nself.Width           = 1920      #Width of window\nself.Height          = 1080      #Height of window\nself.cameraView      = 'left'    #Which camera we view\nself.annotateSize    = 17        #Size of text overlay \nself.textColor       = 'white'   #Color of text overlay\nself.Window          = None      #Coordinates of preview window\nself.Format          = 'h264'    #Video format\nself.streamVideo     = False     #If true, video streams to port\nself.textBackground  = None      #Background for text overlay\nself.cameraFramerate = 24        #Framerate of camera, \nself.propertyArgs    = None      #Property args from command line\nself.cameraAwb       = 'horizon' #Auto white balance, default is horizon for some reason\nself.Quality         = 25        #Quality of recording")

                sys.exit()      
            elif opt in ("-d", "--display"):
                self.Display         = arg
            
            elif opt in ("-s", "--stream"):
                self.streamVideo     = True
            
            elif opt in ("-v", "--view"):
                self.cameraView      = arg
            
            elif opt in ("-as", "--annsize"):
                self.annotateSize    = arg
            
            elif opt in ("-b", "--background"):
                self.textBackground  = arg
            
            elif opt in ("-w", "--width"):
                self.Width           = arg
            
            elif opt in ("-h", "--height"):
                self.Height          = arg
                
            elif opt in ("-f", "--framerate"):
                self.cameraFramerate = arg
                
            elif opt in ("-q", "--quality"):
                self.Quality         = arg
                
            elif opt in ("-vf", "--vflip"):
                self.setVFlip        = True
                
            elif opt in ("-hf", "--hflip"):
                self.setHFlip        = True
            
            elif opt in ("-c", "--color"):
                self.textColor     = arg
                
            elif opt in ("-aw", "--awb"):
                self.cameraAwb       = arg
                
            elif opt in ("fm", "--format"):
                self.Format          = arg
            
            elif opt in ("sp", "--splitter"):
                self.splitterPort    = arg

    def setClvc(self):

        #Sets the correct cmdline property for Clvc

        self.cmdLine = ['cvlc','-q','stream:///dev/stdin','--sout','#standard{access=http,mux=ts,dst=:5001}',':demux=h264','-' ]

    def setDisplay(self):

        if (self.Display.lower() == 'ul'):   # Upper Left Display
                self.Fullscreen = False
                self.Window = (0, 0, 960, 539)

        elif (self.Display.lower() == 'ur'): # Upper Right Display
                self.Fullscreen = False
                self.Window     = (960, 0, 960, 540)
            
        elif (self.Display.lower() == 'll'):   # Lower Left Display
                self.Fullscreen = False
                self.Window     = (0, 540, 960, 540)

        elif (self.Display.lower() == 'lr'):   # Lower Right Display
                self.Fullscreen = False
                self.Window     = (960, 540, 960, 540)

        else:
                self.Fullscreen = True #If it's full or nothing, then we get a fullscreen

    def setAnnotate(self):

        self.gps.formatGps() 
        self.radar.formatRadar()  
    
        if(self.cameraView): #If we have a camera view selected (which we should), then annotate it accordingly
            self.cameraAnnotate = self.cameraView.title() + "  " + \
            self.currentTime + "  " + self.gps.gpsText + "\n" + \
            self.radar.radarText + self.gps.vehicleSpeed
        else:
            self.cameraAnnotate = ""
                         
def main(argv):

    vte = VTECamera() #Create instance

    vte.property.propertyArgs = argv #Our arg inputs are added to propertyArgs attribute for later use

    vte.property.propertyInput() #All arg inputs are now set as object attributes for camera use

    vte.file_manager.log = open(vte.file_manager.logFileOut, "a", 1) #Open file for wr iting

    time.sleep(vte.property.videoDelay) #Camera delay before starting upo

    vte.startCamera() #Initialize camera
    
    while(true):
        vte.loopCamera()
                         
if __name__ == "__main__":

    main(sys.argv[1:])
        
        
