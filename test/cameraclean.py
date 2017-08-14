#!/usr/bin/python3
#

from __future__ import print_function
from datetime import datetime, timedelta, timezone

import picamera
from PIL import Image
from picamera import Color
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

#Currently this file looks good, the only thing I'm questionable on
#is the camera properties input with command arguments. I'm not
#sure if i set it up correctly

class GpsData:
	
		#
		#	This class does all of the gps data handling
		# 		as well as formatting for display use
		#
	
	def setGps(self):
			
			#
			#	Sets gps data based on data we received from http request
			#
			#	Here are a list of variables that we assign:
			#		latFloat: Our latitude coordinates
			#		lonFloat: Our longitude coordinates
			#		currentSpeed: Our current speed, read from the car, included as gps data
			#
			
		self.gpsGet() #Call Getter function to load gps information
		try:
			
			self.latFloat     = self.gpsData["Latitude"]
			self.lonFloat     = self.gpsData["Longitude"] #Assign object attributes from parsed data
			self.currentSpeed = self.gpsData["Speed"]
				
		except Exception as e: #Exception handling, put it in gpsError incase we need to use it later
			print(e)
			self.gpsError     = e
	
	def formatGps(self):
		
			#
			#	We combine all of this data into specific formats to be used
			#	The formatted data is placed in the following attributes:
			#		gpsText: Formatted gps information based on our latFloat and lonFloat
			#		vehicleSpeed: Formatted vehicle speed information based on currentSpeed 
			#
			
		self.setGps()
		try:
			
			self.gpsText      = " Lat: {0:2.6f} ".format(float(self.latFloat)) + \ 
            " Long: {0:2.6f} ".format(float(self.lonFloat))	
			
			self.vehicleSpeed = " VS: {0:<3.0f}".format(float(self.currentSpeed))
	
		except Exception as e:
			print(e)
			self.gpsError     = e
	
class RadarData:
	
		#
		#	This class does all of the radar data handling 
		#		and formatting for display use
		#
	
	def setRadar(self):
			
			#
			#	Sets radar data based on data we received from http request
			#
			#	Here are a list of variables that we assign:
			#		latFloat: Our latitude coordinates
			#		lonFloat: Our longitude coordinates
			#		currentSpeed: Our current speed, read from the car, included as gps data
			#
			
		self.radarGet() #Call getter function to load radar information
		try:
			
			self.patrolSpeed  = str(self.radarData["PatrolSpeed"]) 
			self.lockedTarget = str(self.radarData["LockedTargetSpeed"]) #Assign respective object attributes based on parsed info
			self.targetSpeed  = str(self.radarData["TargetSpeed"])
			self.Antenna      = str(self.radarData["Mode"]["antenna"])
			self.Transmit     = str(self.radarData["Mode"]["transmit"])
			self.Direction    = str(self.radarData["Mode"]["direction"])
				
		except Exception as e:
			print(e)
			self.radarError   = e
	
	def formatRadar(self):
		
			#
			#	We combine all of this data into specific formats to be used
			#	The formatted data is placed in the following attributes:
			#		radarText: Formatted radar information based on all atributes in setRadar
			#
			
		self.setRadar()
		try:
			
			self.radarText = " T: " + self.targetSpeed +  "  " + \
            " L: " + self.lockedTarget + "  " + \
            " P: " + self.patrolSpeed +  "  " + \
			self.Direction
	
		except Exception as e:
			print(e)
			self.gpsError  = e
	
class HttpHandler:
		
		#
		#	This class does all of the HTTP Request handling and
		#		provides the object with json data for both gps
		#		and radar information in their respective ports
		#
	
	def gpsGet(self):
			
			#
			#	HTTP Getter for gps json data
			#
			
		try:
				#	Request data from port 9001
			r = requests.get('http://left.local:9001')
				#	Check status code if success request
			if r.status_code == 200:
					#	Try opening json file we received
				try:
					self.gpsData = json.loads(r.text)
						
				except Exception as e:
					print (e)
					self.gpsError = e
				#	If we got a bad HTTP request		
			else:
				self.gpsError = "Bad HTTP Reqest. Error Code: " + r.status_code
					
		except Exception as e:
			print (e)
			self.gpsError = e
			
	def radarGet(self):
			
			#
			#	HTTP Getter for radar json data
			#
			
		try:
				#	Request data from port 9002
			r = requests.get('http://left.local:9002')
				#	Check status code if success request
			if r.status_code == 200:
					#	Try opening json file we received
				try: 
					self.radarData = json.loads(r.text)
						
				except Exception as e:
					print (e)
					self.radarError = e
				#	If we got a bad HTTP request		
			else:
				self.radarError = "Bad HTTP Reqest. Error Code: " + r.status_code
					
		except Exception as e:
			print (e)
			self.radarError = e			
			
class FileManager:
	
	def rotateCheck(self):
		
		self.currentMinutes = datetime.datetime.now().minute
		
			#	Checks if we are at a multiple of 15 minutes and if our current minutes don't
			#		equal our last rotation
			# 	Make sure self.currentMinutes is an int
			
		if(!(self.currentMinutes % 15)  and  self.currentMinutes != self.lastRotate):
			return True
		
		else:
			return False

		
	def writeFile(self):
	
		self.videoDirectory = self.dataDirectory + '/' + self.cameraView.lower() + '/' #Make video directory
	
		self.videoFile      = self.videoDirectory + self.cameraView + "_" + \ #Combine video file
		dt.datetime.now().strftime('%Y%m%d_%H%M.h264')
		
		self.lastRotate     = dt.datetime.now().strftime('%M') #Set last rotation
		
		self.logData        = dt.datetime.now().strftime('%T [CAMERA]: ') + \ #prepare log data
		"Started recording " + self.videoFile + "\n"
		
		log.write(self.logData) #write to log
	
class VteAnnotate:

	def setAnnotate(self):
	
		self.formatGps() #Get formatted gps info
		self.formatRadar()	#Get formatted radar info
	
		if(self.cameraView): #If we have a camera view selected (which we should), then annotate it accordingly
			self.cameraAnnotate = self.cameraView.title() + "  " + \ 
			self.currentTime + "  " + self.gpsText + "\n" + \ 
			self.radarText + self.vehicleSpeed
		else:
			self.cameraAnnotate = ""
	
	
class CamProperties:


	def propertyInput(self, argv): #This function allows us to input all of our camera properties to be assigned
	
		try:
			opts, args = getopt.getopt(argv, "h:d:s:v:as:b:w:h:f:q:vf:hf:c:aw:fm:sp", ["help", "display=", "stream", "view=", "annsize=", "background=", "width=", "height=", "framerate=", "quality=", "vflip", "hflip", "color=", "awb=", "format=", "splitter="])
		except getopt.GetoptError:
			print ('camera.py -v <camera_view> -d <display> -s')
			sys.exit(2)	
		
		for opt, arg in opts:
			if opt == '-h':
				print ('camera.py -v <camera_view> -d <display> -s')
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
				self.cameraColor     = arg
				
			elif opt in ("-aw", "--awb"):
				self.cameraAwb       = arg
				
			elif opt in ("fm", "--format"):
				self.Format          = arg
			
			elif opt in ("sp", "--splitter")
				self.splitterPort    = arg
		

class DisplayProperties:


	def setDisplay(self):
	
		if (self.Display.lower() == 'ul'):   # Upper Left Display
			self.Fullscreen = False
			self.Window     = (0, 0, 960, 539)
			
        elif (self.Display.lower() == 'ur'):   # Upper Right Display
			self.Fullscreen = False
			self.Window     = (960, 0, 960, 540)
			
        elif (self.Display.lower() == 'll'):   # Lower Left Display
			self.Fullscreen = False
			self.Window     = (0, 540, 960, 540)

        elif (self.Display.lower() == 'lr'):   # Lower Right Display
			self.Fullscreen = False
			self.Window     = (960, 540, 960, 540)

        else:
			self.Fullscreen = True #If it's full, then we get a fullscreen
	
	
class PiCamera():

	#This class handles all functions from the original PiCamera class, like displaying and running

	
	def __init__(self):
		
		self.gpsText      = "NO GPS DATA" #Basic initial values that we need to be set from the get go
		self.vehicleSpeed = "NO GPS DATA"
		self.radarText    = "NO RADAR DATA"
		
		self.currentMinutes = datetime.datetime.now().minute
		
		self.cameraView  = 'left'
		self.streamVideo = False
		self.setVFlip    = False
		self.setHFlip    = False
		self.Display     = 'full'
		
		self.lastRotate  = datetime.datetime.now().minute
		
		self.mainDirectory = "/home/camera/vte"
		self.logDirectory  = self.mainDirectory + "/logs"
		self.dataDirectory = self.mainDirectory + "/data"
		self.logFileOut    = self.logDirectory + "/status.log"
		
		self.videoDelay     = 1
		self.timeoutSeconds = 0.2
		
	def outputDisplay(self):
	
		self.start_preview(self.Fullscreen, self.Window) #Display preview onto screen
	
	def doAnnotate(self):
	
		self.annotate_text = self.cameraAnnotate #annotate text is already set from set annotate function

	def startCamera(self):
	
		self.resolution          = (self.Width, self.Height) #initialization variables for starting the camera
		
		self.framerate           = self.cameraFramerate
		
		self.vflip               = self.setVFlip
		
		self.hflip               = self.setHFlip
		
		self.annotate_text_size  = self.annotateSize
		
		self.annotate_foreground = Color(self.cameraColor.title())
		
		self.awb_mode            = self.cameraAwb
		
	def runClvc(self):
		
		self.cmdline = ['cvlc','-q','stream:///dev/stdin','--sout','#standard{access=http,mux=ts,dst=:5001}',':demux=h264','-' ] #Calls clvc 
	
	def openSubprocess(self):
	
		if(self.streamVideo):
			myvlc = subprocess.Popen(self.cmdline, stdin=subprocess.PIPE) #Opens subprocess for clvc streaming
	
	def runCamera(self):
	
		self.start_recording(self.videoFile, quality = self.Quality, format = self.Format) #start recording to file
		
		if(self.streamVideo):
			self.start_recording(myvlc.stdin, format = self.Format, splitter_port = self.splitterPort) #if we want to stream video, do that as well
			
def main():

#Basic step through of running camera

#Declare Object
#Set Properties
#Run clvc
#Open subprocess for streaming
#FOREVER
#Write log file
#Check display and preview accordingly
#Start recording to file
#Start recording to monitor
#If we aren't ready to rotate, keep annotating stuff on the screen.
#If we are ready to rotate, stop recording, and if we don't want to stream video, stop that too

	with picamera.PiCamera() as camera: 
	
		camera.propertyInput()
		
		camera.log = open(camera.logFileOut, "a", 1)
		time.sleep(camera.videoDelay)
		
		camera.runClcv()
		camera.openSubprocess()
		camera.startCamera()
		
		while(true):
			camera.writeFile()
			camera.setDisplay()
			camera.outputDisplay()
			camera.runCamera()
			
			while not (camera.rotateCheck())
				camera.setAnnotate()
				camera.doAnnotate()
				camera.wait_recording(self.timeoutSeconds)
				
			if(self.streamVideo):
				camera.stop_recording(splitter_port = camera.splitterPort)
			
			sys.exit(0)
		