#!/usr/bin/python

import sys
import time
import signal
import csv
import logging
import argparse
import textwrap

import datetime as dt

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.settings import SettingsWithSidebar
from kivy.uix.recycleview import RecycleView
from kivy.uix.actionbar import ActionBar
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
from kivy.base import stopTouchApp

from vteControl import VTEControl
from logging.handlers import TimedRotatingFileHandler


RED = (1,0,0,1)
GREEN = (0,1,0,1)
BLUE = (0,0,1,1)
YELLOW = (1,1,0,1)
BLACK = (0,0,0,1)
GREY = (1,1,1,1)

class MenuScreen(Screen):
    
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)

        logger.debug ("Menu Screen")

    pass


class SystemButtons(BoxLayout):
    
    def __init__(self, **kwargs):
        super(SystemButtons, self).__init__(**kwargs)
        self.vte = VTEControl()
        self.app = App.get_running_app()

    def systemButtonDispatch(self):

        logger.info ("System Button Dispatch")
        
        #
        #  Determine button operation based on current status
        #
        if (self.app.systemStatus == "OFF"):
            self.app.systemStatus = "STARTING"
            Clock.schedule_once(self.systemButtonStart, 0.25)
        elif (self.app.systemStatus == "DEGRADED"):
            self.app.systemStatus = "STOPPING"
            Clock.schedule_once(self.systemButtonStop, 0.25)
        elif (self.app.systemStatus == "ON"):
            self.app.systemStatus = "STOPPING"
            Clock.schedule_once(self.systemButtonStop, 0.25)

        logger.info ("System Status : " + self.app.systemStatus)

        self.ids.system.background_color = YELLOW

    def systemButtonStart(self, dt):
        logger.info ("Starting System")
        self.vte.startSystem()
        Clock.schedule_once(self.statusSystem, 2)

    def systemButtonStop(self, dt):
        logger.info ("Stopping System")
        self.vte.stopSystem()
        Clock.schedule_once(self.statusSystem, 2)
            
    def statusSystem(self, dt):
        logger.info ("Checking System Status")

        self.app.leftCameraStatus  = self.vte.leftCameraStatus()
        self.app.frontCameraStatus = self.vte.frontCameraStatus()
        self.app.rearCameraStatus  = self.vte.rearCameraStatus()
        self.app.audioStatus       = self.vte.audioStatus()
        self.app.radarStatus       = self.vte.radarStatus()
        self.app.gpsStatus         = self.vte.gpsdStatus()
        self.app.gpsLogStatus      = self.vte.gpsStatus()
        
        #
        # Check to see whether any of of the modules or sub-components are on.
        # If anything is running, then mark the system "ON"
        #

        if (self.app.leftCameraStatus == "ON") and (self.app.frontCameraStatus == "ON") and \
           (self.app.rearCameraStatus == "ON") and (self.app.audioStatus == "ON") and \
           (self.app.radarStatus == "ON") and (self.app.gpsStatus == "ON") and \
           (self.app.gpsLogStatus == "ON"):
            
            self.app.systemStatus = "ON"
            self.ids.system.background_color = GREEN
            
        elif (self.app.leftCameraStatus == "OFF") and (self.app.frontCameraStatus == "OFF") and \
           (self.app.rearCameraStatus == "OFF") and (self.app.audioStatus == "OFF") and \
           (self.app.radarStatus == "OFF") and (self.app.gpsLogStatus == "OFF"):
            
            self.app.systemStatus = "OFF"
            self.ids.system.background_color = RED
            
        else:
            self.app.systemStatus = "DEGRADED"
            self.ids.system.background_color = GREEN

    pass

class CameraViewButtons(BoxLayout):
    
    def __init__(self, **kwargs):
        super(CameraViewButtons, self).__init__(**kwargs)
        self.vte = VTEControl()

    def buttonMultiView(self):
        logger.info ("Toggle Multiview")
        self.vte.toggleMultiView()
        
    def buttonLeftView(self):
        logger.info ("Change Left View")
        self.vte.changeLeftView()
    
    def buttonFrontView(self):
        logger.info ("Change Front View")
        self.vte.changeFrontView()

    def buttonRearView(self):
        logger.info ("Change Rear View")
        self.vte.changeRearView()
        
    def buttonControlView(self):
        logger.info ("Change Control View")
        self.vte.changeControlView()

    pass

class CameraControlButtons(BoxLayout):
    
    def __init__(self, **kwargs):
        super(CameraControlButtons, self).__init__(**kwargs)
        self.vte = VTEControl()
        self.app = App.get_running_app()
    
    def statusLeftCamera(self, dt):
        self.app.leftCameraStatus = self.vte.leftCameraStatus()     
        
    def buttonLeftCam(self):
        if (self.app.leftCameraStatus == "ON"):
            self.app.leftCameraStatus = "OFF"
            self.vte.stopLeftCamera()
            Clock.schedule_once(self.statusLeftCamera, 1)
            
        elif (self.app.leftCameraStatus == "OFF"):
            self.app.leftCameraStatus = "ON"
            self.vte.startLeftCamera()
            Clock.schedule_once(self.statusLeftCamera, 1)

    def statusFrontCamera(self, dt):
        self.app.frontCameraStatus = self.vte.frontCameraStatus()

    def buttonFrontCam(self):
        if (self.app.frontCameraStatus == "ON"):
            self.app.frontCameraStatus = "OFF"
            self.vte.stopFrontCamera()
            Clock.schedule_once(self.statusFrontCamera, 1)
            
        elif (self.app.frontCameraStatus == "OFF"):
            self.app.frontCameraStatus = "ON"
            self.vte.startFrontCamera()
            Clock.schedule_once(self.statusFrontCamera, 1)

    def statusRearCamera(self, dt):
        self.app.rearCameraStatus = self.vte.rearCameraStatus()
        
    def buttonRearCam(self):
        if (self.app.rearCameraStatus == "ON"):
            self.app.rearCameraStatus = "OFF"
            self.vte.stopRearCamera()
            Clock.schedule_once(self.statusRearCamera, 1)
            
        elif (self.app.rearCameraStatus == "OFF"):
            self.app.rearCameraStatus = "ON"
            self.vte.startRearCamera()
            Clock.schedule_once(self.statusRearCamera, 1)
        
    pass

class SubsystemButtons(BoxLayout):
    
    def __init__(self, **kwargs):
        super(SubsystemButtons, self).__init__(**kwargs)
        self.vte = VTEControl()
        self.app = App.get_running_app()

    def statusAudio(self, dt):
        self.app.audioStatus = self.vte.audioStatus()

    def buttonAudio(self):
        if (self.app.audioStatus == "ON"):
            self.app.audioStatus = "OFF"
            self.vte.stopAudio()
            Clock.schedule_once(self.statusAudio, 1)

        elif (self.app.audioStatus == "OFF"):
            self.app.audioStatus = "ON"
            self.vte.startAudio()
            Clock.schedule_once(self.statusAudio, 1)
        
    pass

class DataButtons(BoxLayout):
    
    def __init__(self, **kwargs):
        super(DataButtons, self).__init__(**kwargs)
        
    pass


class EventButtons(BoxLayout):
    
    def __init__(self, **kwargs):
        super(EventButtons, self).__init__(**kwargs)

    def eventWrite(self, message):
    
        current_timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        #  Open violations file for appending
        
        path = '/home/camera/vte/data/radar/'
        file = open( path +"violations.csv", "a", 1) # non-blocking

        #
        #  Could check radar information and record it.  For now just put placeholder zeros
        #
        
        file.write(current_timestamp + ", 0, 0, 0, 0, 0, 0, " + message + '\n')
        file.close()
        return

    def eventSpeeding(self):
        logger.info ("Record Speeding Event")
        self.ids.event_speeding.background_color = GREEN
        self.eventWrite('speeding')
        Clock.schedule_once(self.eventSpeedingOff, 1)

    def eventSpeedingOff(self, dt):
        self.ids.event_speeding.background_color = GREY

    def eventFailStop(self):
        logger.info ("Record Failure to Stop/Yield Event")
        self.ids.event_failstop.background_color = GREEN
        self.eventWrite('failstop')
        Clock.schedule_once(self.eventFailStopOff, 1)

    def eventFailStopOff(self, dt):
        self.ids.event_failstop.background_color = GREY

    def eventLaneChange(self):
        logger.info ("Record Illegal Lane Change Event")
        self.ids.event_lanechange.background_color = GREEN
        self.eventWrite('lanechange')
        Clock.schedule_once(self.eventLaneChangeOff, 1)
                   
    def eventLaneChangeOff(self, dt):
        self.ids.event_lanechange.background_color = GREY

    def eventReckless(self):
        logger.info ("Record Reckless Driving Event")
        self.ids.event_reckless.background_color = GREEN
        self.eventWrite('reckless')
        Clock.schedule_once(self.eventRecklessOff, 1)
                   
    def eventRecklessOff(self, dt):
        self.ids.event_reckless.background_color = GREY

    pass

class ButtonPanel(BoxLayout):
    
    def __init__(self, **kwargs):
        super(ButtonPanel, self).__init__(**kwargs)
        
    pass

class TopBar(ActionBar):
    
    def __init__(self, **kwargs):
        super(TopBar, self).__init__(**kwargs)

    pass

class StatusBar(BoxLayout):

    currentTime       = StringProperty()
    
    def __init__(self, **kwargs):
        super(StatusBar, self).__init__(**kwargs)
        self.currentTime = str(time.asctime())
        Clock.schedule_once(self.updateTime, 1)

    def updateTime(self, dt):
        self.currentTime = str(time.asctime())
        Clock.schedule_once(self.updateTime, 1)
        
    pass

class FrontScreen(Screen):

    def __init__(self, **kwargs):
        super(FrontScreen, self).__init__(**kwargs)
        
        self.vte = VTEControl()

    def buttonControlView(self):
        logger.debug ("Change Control View")
        self.vte.changeControlView()
    
    pass

class LeftScreen(Screen):
    
    def __init__(self, **kwargs):
        super(LeftScreen, self).__init__(**kwargs)
        
        self.vte = VTEControl()

    def buttonControlView(self):
        logger.debug ("Change Control View")
        self.vte.changeControlView()
    
    pass

class RearScreen(Screen):
    
    def __init__(self, **kwargs):
        super(RearScreen, self).__init__(**kwargs)
        
        self.vte = VTEControl()

    def buttonControlView(self):
        logger.debug ("Change Control View")
        self.vte.changeControlView()
    
    pass

class FrontQScreen(Screen):
    pass

class LeftQScreen(Screen):
    pass

class RearQScreen(Screen):
    pass

class QuadScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class UploadScreen(Screen):

    #
    #  Progress Bars
    #


    vaultStatus   = StringProperty()
    controlStatus = StringProperty()
    leftStatus    = StringProperty()
    frontStatus   = StringProperty()
    rearStatus    = StringProperty()

    controlInfo  = StringProperty()
    leftInfo     = StringProperty()
    frontInfo    = StringProperty()
    rearInfo     = StringProperty()

    pbControl = ProgressBar()
    pbLeft    = ProgressBar()
    pbFront   = ProgressBar()
    pbRear    = ProgressBar()
    
    def __init__(self, **kwargs):
        super(UploadScreen, self).__init__(**kwargs)
        self.vte = VTEControl()

        self.vaultStatus = ""
        self.controlStatus = ""
        self.leftStatus = ""
        self.frontStatus = ""
        self.rearStatus = ""

        self.controlInfo = ""
        self.leftInfo = ""
        self.frontInfo = ""
        self.rearInfo = ""

        self.pbControl.value = 0
        self.pbLeft.value    = 0
        self.pbFront.value   = 0
        self.pbRear.value    = 0

    def uploadData(self):
        logger.info ("Uploading Data")
        self.vte.startHomebase()
        logger.info ("Started Homebase")
        self.event=Clock.schedule_interval(self.fetchRsyncStatus, 5.0)

    def fetchRsyncStatus(self, dt):

        rsyncStatus = self.vte.getRsyncData()
        
        self.vaultStatus   = rsyncStatus["vault"]["status"]
        self.controlStatus = rsyncStatus["control"]["status"]
        self.leftStatus    = rsyncStatus["left"]["status"]
        self.frontStatus   = rsyncStatus["front"]["status"]
        self.rearStatus    = rsyncStatus["rear"]["status"]

        self.controlInfo  = rsyncStatus["control"]["info"]
        self.leftInfo     = rsyncStatus["left"]["info"]
        self.frontInfo    = rsyncStatus["front"]["info"]
        self.rearInfo     = rsyncStatus["rear"]["info"]
            
        self.pbControl.value = rsyncStatus["control"]["progress"]
        self.pbLeft.value    = rsyncStatus["left"]["progress"]
        self.pbFront.value   = rsyncStatus["front"]["progress"]
        self.pbRear.value    = rsyncStatus["rear"]["progress"]

    def cancelUploadData(self):
        logger.info ("Cancel Uploading Data")
        self.event.cancel()
        self.vte.stopHomebase()
    pass

class RadarData(GridLayout):

    def __init__(self, **kwargs):
        super(RadarData, self).__init__(**kwargs)
        
    pass
    
class RadarScreen(Screen):

    manager = ObjectProperty(None)
    col1 = ListProperty()   # Labels
    col2 = ListProperty()   # Radar Data

    def __init__(self, **kwargs):
        super(RadarScreen, self).__init__(**kwargs)

        self.col1 = []
        self.col2 = []
        self.col1.append("Patrol Speed")
        self.col1.append("Locked Target Speed")
        self.col1.append("Target Speed")
        self.col1.append("Max Target Speed")
        self.col1.append("Antenna")
        self.col1.append("Transmit Mode")
        self.col1.append("Direction")
        
        self.vte = VTEControl()

    def radarData(self):
        self.event=Clock.schedule_interval(self.fetchRadarData, 0.3)

    def fetchRadarData(self,dt):
        self.col2 = []
        radarData = self.vte.getRadarData()
        try:
            
            self.col2.append(str(radarData["PatrolSpeed"]))
            self.col2.append(str(radarData["LockedTargetSpeed"]))
            self.col2.append(str(radarData["TargetSpeed"]))
            self.col2.append(str(radarData["MaxTargetSpeed"]))
            self.col2.append(str(radarData["Mode"]["antenna"]))
            self.col2.append(str(radarData["Mode"]["transmit"]))
            self.col2.append(str(radarData["Mode"]["direction"]))
            
        except Exception as e:
            self.col2 = ["Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown"]

    def cancelRadarData(self):
        self.event.cancel()

    pass

class EventSummaryScreen(Screen):

    data = ListProperty()
    status = StringProperty()
    
    def __init__(self, **kwargs):
        super(EventSummaryScreen, self).__init__(**kwargs)

    def eventDataStatus(self):
        self.status = "Retrieving Data..."

    def eventData(self):
        logger.debug ("Fetching Event Data")
        
        self.data = []

        #  Open violations file for reading
        
        path = '/home/camera/vte/data/radar/'
        file=open( path +"violations.csv", "r")
        reader = csv.reader(file, skipinitialspace=True)

        lastTransmit = dt.datetime.min
        lastHold     = dt.datetime.min
        expectTransmit = True;
        expectHold     = False;
        
        for field in reader:
            radarTime         = dt.datetime.strptime(field[0], '%Y-%m-%d %H:%M:%S.%f')
            targetSpeed       = field[1]
            patrolSpeed       = field[2]
            lockedTargetSpeed = field[3]
            maxSpeed          = field[4]
            transmitMode      = field[7]
            
            if (transmitMode == 'transmit') and expectTransmit:
                lastTransmit   = radarTime
                expectTransmit = False
                expectHold     = True
            elif (transmitMode == 'hold') and expectHold:
                lastHold       = radarTime
                expectTransmit = True
                expectHold     = False

                #
                #  Print out event (transmit to hold)
                #
                self.data.append(dt.datetime.strftime(lastTransmit,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(dt.datetime.strftime(lastHold,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(lockedTargetSpeed)
                self.data.append(maxSpeed)
                self.data.append(patrolSpeed)
                self.data.append("Speeding")
            elif (transmitMode == 'speeding'):
                self.data.append(dt.datetime.strftime(radarTime,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(dt.datetime.strftime(radarTime,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(lockedTargetSpeed)
                self.data.append(maxSpeed)
                self.data.append(patrolSpeed)
                self.data.append("Speeding")
            elif (transmitMode == 'failstop'):
                self.data.append(dt.datetime.strftime(radarTime,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(dt.datetime.strftime(radarTime,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(lockedTargetSpeed)
                self.data.append(maxSpeed)
                self.data.append(patrolSpeed)
                self.data.append("Failure to Stop/Yield")
            elif (transmitMode == 'lanechange'):
                self.data.append(dt.datetime.strftime(radarTime,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(dt.datetime.strftime(radarTime,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(lockedTargetSpeed)
                self.data.append(maxSpeed)
                self.data.append(patrolSpeed)
                self.data.append("Illegal Lane Change")
            elif (transmitMode == 'reckless'):
                self.data.append(dt.datetime.strftime(radarTime,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(dt.datetime.strftime(radarTime,'%a %b-%d  %I:%M:%S %p'))
                self.data.append(lockedTargetSpeed)
                self.data.append(maxSpeed)
                self.data.append(patrolSpeed)
                self.data.append("Reckless Driving")

        self.status = ""

class SystemStatusScreen(Screen):

    col1 = ListProperty()   # Labels
    col2 = ListProperty()   # Control Processor
    col3 = ListProperty()   # Left Processor
    col4 = ListProperty()   # Front Processor
    col5 = ListProperty()   # Rear Processor
    col6 = ListProperty()   # Future Right PRocessor
    
    status = StringProperty()
    
    def __init__(self, **kwargs):
        super(SystemStatusScreen, self).__init__(**kwargs)

        self.col1 = []
        self.col1.append("Hostname")
        self.col1.append("Local IP Address")
        self.col1.append("Wireless IP Address")
        self.col1.append("Temperature")
        self.col1.append("CPU Speed")
        self.col1.append("Uptime")
        self.col1.append("CPU Usage")
        self.col1.append("Memory Usage")
        self.col1.append("Root Disk Usage")
        self.col1.append("Data Disk Usage")
        self.col1.append("Voltage")
        
        self.vte = VTEControl()
        

    def systemData(self):
        self.status = "Retrieving Data..."

    def fetchSystemData(self):
        
        self.status = "Retrieving Data..."
        
        self.col2 = []
        self.col3 = []
        self.col4 = []
        self.col5 = []
        self.col6 = []

        try:
            systemData = self.vte.getServerURL()

            self.col2 = systemData["Control"]
            self.col3 = systemData["Left"]
            self.col4 = systemData["Front"]
            self.col5 = systemData["Rear"]
            self.status = ""
        except:
            self.status = "Unable to Retrieve Data..."
            
        
    def cancelSystemData(self):
        self.event.cancel()

    pass
    
class ShutdownScreen(Screen):

    pb = ProgressBar(max=100)

# this will update the graphics automatically (75% done)
#  pb.value = 750
    
    def __init__(self, **kwargs):
        super(ShutdownScreen, self).__init__(**kwargs)

    def doShutdown(self):
        logger.info ("Shutting Down System...")
        stopTouchApp()

    pass
        

class vteGUI(App):

    mainDirectory    = "/home/camera/vte"
    logDirectory     = mainDirectory + "/logs"
    logFileName      = logDirectory + "/status"
    
    systemButton      = StringProperty()
    leftCameraButton  = StringProperty()
    frontCameraButton = StringProperty()
    rearCameraButton  = StringProperty()
    audioButton       = StringProperty()

    systemStatus      = StringProperty()
    leftCameraStatus  = StringProperty()
    frontCameraStatus = StringProperty()
    rearCameraStatus  = StringProperty()
    audioStatus       = StringProperty()
    radarStatus       = StringProperty()
    gpsStatus         = StringProperty()
    gpsLogStatus      = StringProperty()
    
    def __init__(self, **kwargs):
        super(vteGUI, self).__init__(**kwargs)

        logger.debug ("Initializing VTE Application State")

        self.vte = VTEControl()
        
        self.vte.changeControlView()
        
        self.leftCameraStatus  = self.vte.leftCameraStatus()
        self.frontCameraStatus = self.vte.frontCameraStatus()
        self.rearCameraStatus  = self.vte.rearCameraStatus()
        self.audioStatus       = self.vte.audioStatus()
        self.radarStatus       = self.vte.radarStatus()
        self.gpsStatus         = self.vte.gpsdStatus()
        self.gpsLogStatus      = self.vte.gpsStatus()

        
        #
        # Check to see whether any of of the modules or sub-components are on.
        # If anything is running, then mark the system "ON"
        #

        if self.leftCameraStatus == "ON":
            self.systemStatus = "ON"
        elif self.frontCameraStatus == "ON":
            self.systemStatus = "ON"
        elif self.rearCameraStatus == "ON":
            self.systemStatus = "ON"
        else:
            self.systemStatus = "OFF"

        logger.info ("System Status       : " + self.systemStatus)
        logger.info ("Left Camera Status  : " + self.leftCameraStatus)
        logger.info ("Front Camera Status : " + self.frontCameraStatus)
        logger.info ("Rear Camera Status  : " + self.rearCameraStatus)
        logger.info ("Audio Status        : " + self.audioStatus)
        logger.info ("Radar Status        : " + self.radarStatus)
        logger.info ("GPS Status          : " + self.gpsStatus)
        logger.info ("GPS Logger Status   : " + self.gpsLogStatus)

        buttonStatus=["ON", "OFF", "ON", "OFF", "ON"]
        self.vte.postButtonState(buttonStatus)
        
    def build(self):
        return Builder.load_file('vte.kv')

    def on_stop(self):
        logger.info ("Stopping Application")
        self.vte.stopSystem()
        time.sleep(2)
        sys.exit(0)

    def signal_handler(signal, frame):
        logger.info ('Ctrl+C Pressed')
        App.get_running_app().stop()
        sys.exit(0)

if __name__ == '__main__':

    #
    #  Parse Command Line Options
    #

    
    parser = argparse.ArgumentParser(prog='vtegui.py',
                 formatter_class=argparse.RawDescriptionHelpFormatter,
                 description='Video Taffic Enforcement - GUI - Version 0.1',
                 epilog=textwrap.dedent('''\
                    Notes
                    -------------------------------------------------------------------------------------
                    VTE GUI
                    -------------------------------------------------------------------------------------
                    '''))

    parser.add_argument('-v', '--debug', action='store_true', help="Turn on debug mode for logging")
    args = parser.parse_args()
    
    #
    #  Configure Logging
    #
    FORMAT  = 'GUI: %(asctime)-15s: %(levelname)-5s: %(message)s'
    logger  = logging.getLogger('status')
    handler = logging.handlers.TimedRotatingFileHandler(vteGUI.logFileName, when='midnight')
    
    handler.setFormatter(logging.Formatter(FORMAT))

    if (args.debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.addHandler(handler)
                        
    logger.info ("Starting GUI")
    logger.debug (vars(args))
    
    try:
        vteGUI().run()
    
    #
    #  Graceful shutdown of gui
    #
    except (KeyboardInterrupt, SystemExit):
        logger.debug ('Main Exception Handler')
        sys.exit(0)
        
    except Exception:
        import traceback
        logger.debug ('catch all exception handler')
