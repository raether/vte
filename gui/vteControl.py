#!/usr/bin/python3

import subprocess
import sys
import json
import requests
import logging
import socket
import re

logger = logging.getLogger('status')

class VTEControl():

    #
    # Constant Definitions
    #
    FRONT_HOST   = "front.local"
    LEFT_HOST    = "left.local"
    REAR_HOST    = "rear.local"
    CONTROL_HOST = "control.local"

    CAMERA_CMD   = "pgrep -f camera.py"
    GPSD_CMD     = ["pgrep", "gpsd"]
    GPS_CMD      = ["pgrep", "-f", "gps_logger.py"]
    RADAR_CMD    = ["pgrep", "-f", "radar.py"]
    HOMEBASE_CMD = ["pgrep", "-f", "homebase.py"]
    FAN_CMD      = "pgrep -f fan.py"
    AUDIO_CMD    = ["pgrep", "-f", "audio.py"]
    GUI_CMD      = ["pgrep", "-f", "vtegui.py"]
    NAVIT_CMD    = "pgrep navit"
    METRICS_CMD  = "/home/camera/vte/scripts/perfMetrics.sh"
    CAM_METRICS_CMD  = "/home/camera/vte/scripts/perfMetricsCamera.sh"

    START_FRONT_CAM = "/home/camera/vte/scripts/camera.py --vflip --hflip front > /dev/null 2>&1 &"
    START_LEFT_CAM  = "/home/camera/vte/scripts/camera.py left > /dev/null 2>&1 &"
    START_REAR_CAM  = "/home/camera/vte/scripts/camera.py rear > /dev/null 2>&1 &"
    STOP_CAMERA     = "pkill --signal SIGTERM -f camera.py"

    START_AUDIO  = ["/home/camera/vte/scripts/audio.py"]
    STOP_AUDIO   = ["pkill", "--signal", "SIGTERM", "-f", "audio.py"]
    STOP_AUDIO2  = ["pkill", "--signal", "SIGTERM", "-f", "arecord"]

    START_GPS    = ["sudo", "service", "gpsd", "restart"]
    
    START_GPSLOG = ["/home/camera/vte/scripts/gps_logger.py"]
    STOP_GPSLOG  = ["pkill", "--signal", "SIGTERM", "-f", "gps_logger.py"]

    START_RADAR  = ["/home/camera/vte/scripts/radar.py"]
    STOP_RADAR   = ["pkill", "--signal", "SIGTERM", "-f", "radar.py"]

    START_HOMEBASE  = ["/home/camera/vte/scripts/homebase.py"]
    STOP_HOMEBASE   = ["pkill", "--signal", "SIGTERM", "-f", "homebase.py"]

    CONTROL_VIEW = ["irsend", "--count=2", "SEND_ONCE", "zettaguard", "IN4"]
    LEFT_VIEW    = ["irsend", "--count=2", "SEND_ONCE", "zettaguard", "IN3"]
    FRONT_VIEW   = ["irsend", "--count=2", "SEND_ONCE", "zettaguard", "IN2"]
    REAR_VIEW    = ["irsend", "--count=2", "SEND_ONCE", "zettaguard", "IN1"]
    PIP_TOGGLE   = ["irsend", "SEND_ONCE", "zettaguard", "PIP"]

    radarURL      = "http://control.local:9002"
    watchdogURL   = "http://control.local:9003"
    
    def __init__(self):
        pass
        
    def audioRunning(self):
        ssh = subprocess.Popen(VTEControl.AUDIO_CMD,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            return False
        else:

            return True

    def audioStatus(self):
        if self.audioRunning():
            return "ON"
        else:
            return "OFF"

    def radarRunning(self):
        ssh = subprocess.Popen(VTEControl.RADAR_CMD,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            return False
        else:
            return True

    def radarStatus(self):
        if self.radarRunning():
            return "ON"
        else:
            return "OFF"

    def guiRunning(self):
        ssh = subprocess.Popen(VTEControl.GUI_CMD,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            return False
        else:
            return True

    def guiStatus(self):
        if self.guiRunning():
            return "ON"
        else:
            return "OFF"

    def gpsLoggerRunning(self):
        ssh = subprocess.Popen(VTEControl.GPS_CMD,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            return False
        else:
            return True

    def gpsStatus(self):
        if self.gpsLoggerRunning():
            return "ON"
        else:
            return "OFF"
        
    def gpsDaemonRunning(self):
        ssh = subprocess.Popen(VTEControl.GPSD_CMD,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            return False
        else:
            return True

    def gpsdStatus(self):
        if self.gpsDaemonRunning():
            return "ON"
        else:
            return "OFF"

    def cameraOn(self, cameraView):
        ssh = subprocess.Popen(["ssh", "%s" % cameraView, VTEControl.CAMERA_CMD],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            return False
        else:
            return True

    def frontCameraStatus(self):
        if self.cameraOn(VTEControl.FRONT_HOST):
            return "ON"
        else:
            return "OFF"

    def rearCameraStatus(self):
        if self.cameraOn(VTEControl.REAR_HOST):
            return "ON"
        else:
            return "OFF"

    def leftCameraStatus(self):
        if self.cameraOn(VTEControl.LEFT_HOST):
            return "ON"
        else:
            return "OFF"

    def cameraOff(self, cameraView):
        ssh = subprocess.Popen(["ssh", "%s" % cameraView, VTEControl.STOP_CAMERA],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        return True

    def startLeftCamera(self):
        if not self.cameraOn(VTEControl.LEFT_HOST):
            logger.info("Starting Left Camera")
            ssh = subprocess.Popen(["ssh", "%s" % VTEControl.LEFT_HOST, VTEControl.START_LEFT_CAM],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    def stopLeftCamera(self):
        logger.info("Stopping Left Camera")
        retval = self.cameraOff(VTEControl.LEFT_HOST)
    
    def startFrontCamera(self):
        if not self.cameraOn(VTEControl.FRONT_HOST):
            logger.info ("Starting Front Camera")
            ssh = subprocess.Popen(["ssh", "%s" % VTEControl.FRONT_HOST, VTEControl.START_FRONT_CAM],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    def stopFrontCamera(self):
        logger.info ("Stopping Front Camera")
        retval = self.cameraOff(VTEControl.FRONT_HOST)
    
    def startRearCamera(self):
        if not self.cameraOn(VTEControl.REAR_HOST):
            logger.info ("Starting Rear Camera")
            ssh = subprocess.Popen(["ssh", "%s" % VTEControl.REAR_HOST, VTEControl.START_REAR_CAM],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    def stopRearCamera(self):
        logger.info ("Stopping Rear Camera")
        retval = self.cameraOff(VTEControl.REAR_HOST)
    
    def startAudio(self):
        if not self.audioRunning():
            logger.info ("Starting Audio")
            ssh = subprocess.Popen(VTEControl.START_AUDIO,
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    def stopAudio(self):
        logger.info ("Stopping Audio")
        #
        #  Kill the audio.py process
        #
        ssh = subprocess.Popen(VTEControl.STOP_AUDIO,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        #
        #  Also kill the arecord process which is running as a separate process
        #
        ssh = subprocess.Popen(VTEControl.STOP_AUDIO2,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    
    def startGPS(self):
        logger.info ("Starting GPS")
        if not self.gpsDaemonRunning():
            ssh = subprocess.Popen(VTEControl.START_GPS,
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            
        if not self.gpsLoggerRunning():
            ssh = subprocess.Popen(VTEControl.START_GPSLOG,
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    def stopGPS(self):
        logger.info ("Stopping GPS")
        ssh = subprocess.Popen(VTEControl.STOP_GPSLOG,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    def startRadar(self):
        if not self.radarRunning():
            logger.info ("Starting Radar")
            ssh = subprocess.Popen(VTEControl.START_RADAR,
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    def stopRadar(self):
        logger.info ("Stopping Radar")
        ssh = subprocess.Popen(VTEControl.STOP_RADAR,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    
    
    def startSystem(self):
        logger.info("Starting System")
        self.startFrontCamera()
        self.startLeftCamera()
        self.startRearCamera()
        self.startAudio()
        self.startGPS()
        self.startRadar()

    def stopSystem(self):
        logger.info("Stopping System")
        self.stopFrontCamera()
        self.stopLeftCamera()
        self.stopRearCamera()
        self.stopAudio()
        self.stopGPS()
        self.stopRadar()

    def changeFrontView(self):
        logger.info ("Front View")
        retval = subprocess.Popen(VTEControl.FRONT_VIEW,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    def changeLeftView(self):
        logger.info ("Left View")
        retval = subprocess.Popen(VTEControl.LEFT_VIEW,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    def changeRearView(self):
        logger.info ("Rear View")
        retval = subprocess.Popen(VTEControl.REAR_VIEW,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        
    def changeControlView(self):
        logger.info ("Control View")
        retval = subprocess.Popen(VTEControl.CONTROL_VIEW,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    def toggleMultiView(self):
        logger.info ("Toggle PIP")
        retval = subprocess.Popen(VTEControl.PIP_TOGGLE,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    def radarGet(self):
        
        #
        #   HTTP Getter for radar json data
        #
        
        try:
            #   Request data from radar URL
            r = requests.get(VTEControl.radarURL, timeout=0.1)
            
            #   Check status code if success request
            if r.status_code == 200:
                #   Try opening json file we received
                try: 
                    self.radarData = json.loads(r.text)
                        
                except Exception as e:
                    logger.error ("Error Reading JSON File from Radar: %s", e)    
            else:
                #
                #  Bad HTTP Request
                #
                logger.error ("Bad Radar HTTP Reqest. Error Code: " + r.status_code)
                    
        except Exception as e:
            logger.error ("Radar Exception 1: %s", e)

    def getRadarData(self):
    
        #
        #   We combine all of this data into specific formats to be used
        #   The formatted data is placed in the following attributes:
        #       radarText: Formatted radar information based on all atributes in setRadar
        #
        
        self.radarGet() # Call getter function to load radar information
        try:
            return self.radarData

        except Exception as e:
            logger.error ("Radar Exception 2: %s", e)

    def getServerURL(self):
        
        #
        #   HTTP Getter for system watchdog json data
        #
        
        try:
            #   Request data from radar URL
            r = requests.get(VTEControl.watchdogURL, timeout=0.1)
            
            #   Check status code if success request
            if r.status_code == 200:
                #   Try opening json file we received
                try: 
                    systemData = json.loads(r.text)
                    return(systemData)
                        
                except Exception as e:
                    logger.error ("Error Reading JSON File from Watchdog: %s", e)    
            else:
                #
                #  Bad HTTP Request
                #
                logger.error ("Bad Watchdog HTTP Reqest. Error Code: " + r.status_code)
                    
        except Exception as e:
            logger.error ("Watchdog Server Information Exception : %s", e)

    def getServerData(self, hostname):

        logger.debug ("Getting Server Data")

        if (hostname == VTEControl.CONTROL_HOST):  
            p = subprocess.Popen([VTEControl.METRICS_CMD],
                        shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        elif (hostname == VTEControl.FRONT_HOST):
            p = subprocess.Popen(["ssh", "%s" % VTEControl.FRONT_HOST, VTEControl.CAM_METRICS_CMD],
                        shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        elif (hostname == VTEControl.LEFT_HOST):
            p = subprocess.Popen(["ssh", "%s" % VTEControl.LEFT_HOST, VTEControl.CAM_METRICS_CMD],
                        shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        elif (hostname == VTEControl.REAR_HOST):
            p = subprocess.Popen(["ssh", "%s" % VTEControl.REAR_HOST, VTEControl.CAM_METRICS_CMD],
                        shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        else:
            return([])
        
        metrics, err = p.communicate()
        metricsList = metrics.split(",")
        return(metricsList)

    def postButtonState(self, buttonState):
    
        # defining the api-endpoint  
        ENDPOINT = "http://control.local:9003/"

        #
        #  Parse out button state
        #
        
        systemButton = buttonState[0]
        leftButton   = buttonState[1]
        frontButton  = buttonState[2]
        rearButton   = buttonState[3]
        audioButton  = buttonState[4]
          
        # data to be sent to api 
        data = json.dumps({'system': systemButton,
                           'left'  : leftButton,
                           'front' : frontButton,
                           'rear'  : rearButton,
                           'audio' : audioButton})

        try:
            # sending post request and saving response as response object 
            r = requests.post(url = ENDPOINT, data = data)
            
            # extracting response text  
            return_url = r.text 
            logger.debug("The return URL is:%s"%return_url) 
        except:
            return

    def homebaseRunning(self):
        ssh = subprocess.Popen(VTEControl.HOMEBASE_CMD, shell=False,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            return False
        else:
            return True
        
    def startHomebase(self):
        if not self.homebaseRunning():
            logger.info ("Starting Homebase")
            ssh = subprocess.Popen(VTEControl.START_HOMEBASE, shell=False,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stopHomebase(self):
        logger.info ("Stopping Homebase")
        ssh = subprocess.Popen(VTEControl.STOP_HOMEBASE, shell=False,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    def getRsyncData(self):
    
        # defining the api-endpoint  
        ENDPOINT = "http://control.local:9004/"

        #
        #   HTTP Getter for rsync status
        #
        
        try:
            #   Request data from radar URL
            r = requests.get(ENDPOINT, timeout=0.1)
            
            #   Check status code if success request
            if r.status_code == 200:
                #   Try opening json file we received
                try: 
                    rsyncStatus = json.loads(r.text)
                    return(rsyncStatus)
                        
                except Exception as e:
                    return([])   
            else:
                #
                #  Bad HTTP Request
                #
                logger.error ("Homebase Server Error") 
                return([])
                    
        except Exception as e:
            return([])
