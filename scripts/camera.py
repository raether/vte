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

import socket
import select
import time
import json
import requests

import subprocess

main_directory = "/home/camera/vte"
log_directory = main_directory + "/logs"
data_directory = main_directory + "/data"
logfile_out = log_directory + "/status.log"

video_delay = 1
    
#################################################################################################################
#
#  These functions defines the text that is overlayed on the video

def gps_annotate():
    
    try:
        r = requests.get('http://left.local:9001')
        if r.status_code == 200:
            try:
                data = json.loads(r.text)
                lat_float = data["Latitude"]
                lon_float = data["Longitude"]
            except Exception as e:
                print (e)  
        else:
            gps_text = "NO GPS DATA"
            return gps_text
    except:
        gps_text = "NO GPS DATA"
        return gps_text

    gps_text = " Lat: {0:2.6f} ".format(float(lat_float)) + \
               " Long: {0:2.6f} ".format(float(lon_float))

    return gps_text

def gps_vehicle_speed():
    
    try:
        r = requests.get('http://left.local:9001')
        if r.status_code == 200:
            try:
                data = json.loads(r.text)
                current_speed = data["Speed"]
            except Exception as e:
                print (e)  
        else:
            vehicle_speed = "NO GPS DATA"
            return vehicle_speed
    except:
        vehicle_speed = "NO GPS DATA"
        return vehicle_speed

    vehicle_speed = " VS: {0:<3.0f}".format(float(current_speed))

    return vehicle_speed

def radar_annotate():

    try:
        r = requests.get('http://left.local:9002')
        if r.status_code == 200:
            data = json.loads(r.text)
            patrol_speed  = str(data["PatrolSpeed"])
            locked_target = str(data["LockedTargetSpeed"])
            target_speed  = str(data["TargetSpeed"])
            antenna       = str(data["Mode"]["antenna"])
            transmit      = str(data["Mode"]["transmit"])
            direction     = str(data["Mode"]["direction"])
        else:
            radar_text = "NO RADAR DATA    "
            return radar_text
    except:
        radar_text = "NO RADAR DATA    "
        return radar_text

    radar_text = " T: " + target_speed +  "  " + \
                 " L: " + locked_target + "  " + \
                 " P: " + patrol_speed +  "  " + \
                 direction

    return radar_text

def vte_annotate():

    global camera_view

    current_time = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if (camera_view == "front"):
        gps_text = gps_annotate()
        radar_text = radar_annotate()
        vehicle_speed = gps_vehicle_speed()
        camera_annotate = " Front   " + current_time + "   " + gps_text + "\n" + radar_text + vehicle_speed
    elif (camera_view == "rear"):
        gps_text = gps_annotate()
        radar_text = radar_annotate()
        vehicle_speed = gps_vehicle_speed()
        camera_annotate = " Rear   " + current_time + "   " + gps_text + "\n" + radar_text + vehicle_speed
    elif (camera_view == "left"):
        gps_text = gps_annotate()
        radar_text = radar_annotate()
        vehicle_speed = gps_vehicle_speed()
        camera_annotate = "\n Left   " + current_time + "   " + gps_text + "\n" + radar_text + vehicle_speed
    else:
        camera_annotate = ""

    return camera_annotate

#
#  This function should be rewritten to track last_rotate as a property on the object.
#  It should not have to be passed into the function.
#
def ready_to_rotate(last_rotate) :
    current_minutes = dt.datetime.now().strftime('%M')
    if (current_minutes == '00') or \
       (current_minutes == '15') or \
       (current_minutes == '30') or \
       (current_minutes == '45'):
        if (current_minutes != last_rotate):
            return True
        else:
            return False
    else:
        return False
                 
def start_camera():

    global camera_view
    global picam_annotate_size
    global picam_text_background
    global picam_width
    global picam_height
    global picam_framerate
    global picam_quality 
    global video_directory
    global display
    global stream_video
    global set_vflip
    global set_hflip
    global log
    


    with picamera.PiCamera() as camera:

        #
        #  set camera properties
        #
        camera.resolution = (picam_width, picam_height)
        camera.framerate = picam_framerate
        if (set_vflip):
            camera.vflip = True
        if (set_hflip):
            camera.hflip = True
        camera.annotate_text_size = picam_annotate_size
        camera.annotate_foreground = Color('white')
        # camera.annotate_background = Color('Black')
        # camera.annotate_frame_num = True
        camera.awb_mode = 'horizon'

        cmdline = ['cvlc','-q','stream:///dev/stdin','--sout','#standard{access=http,mux=ts,dst=:5001}',':demux=h264','-' ]
        #
        #  Alternative cmdline for sending RTP stream
        #  'rtp{sdp=rtsp://:5001/video}','--sout-rtp-caching=200'
        #
        if (stream_video):
            myvlc = subprocess.Popen(cmdline, stdin=subprocess.PIPE)

        #
        #  Main loop for recording video
        #
        while True:
        
            video_file = video_directory + camera_view + "_" + dt.datetime.now().strftime('%Y%m%d_%H%M.h264')
            last_rotate = dt.datetime.now().strftime('%M')
            log_data = dt.datetime.now().strftime('%T [CAMERA]: ') + "Started recording " + video_file + "\n"
            log.write(log_data)
            
            #
            #  Set the preview screen location on the HDMI Display
            #

            if (display == 'full'):   # Full Screen Display
                camera.start_preview(fullscreen=True)               
            elif (display == 'ul'):   # Upper Left Display
                camera.start_preview(fullscreen=False, window = (0, 0, 960, 539))
            elif (display == 'ur'):   # Upper Right Display
                camera.start_preview(fullscreen=False, window = (960, 0, 960, 540))
            elif (display == 'll'):   # Lower Left Display
                camera.start_preview(fullscreen=False, window = (0, 540, 960, 540))
            elif (display == 'lr'):   # Lower Right Display
                camera.start_preview(fullscreen=False, window = (960, 540, 960, 540))
            else:
                camera.start_preview(fullscreen=True)
            
            #
            #  Start recording the video based on the camera properties
            #
            camera.start_recording(video_file, quality=picam_quality, format='h264')
            #
            #  Start a h.264 stream to the http port
            #
            if (stream_video):
                camera.start_recording(myvlc.stdin, format='h264', splitter_port=2)
        
            start = dt.datetime.now()
            #
            #  Record video only for the picam_time duration.  Then start a new file.
            #
            while not ready_to_rotate(last_rotate):   
                camera.annotate_text = vte_annotate()
                camera.wait_recording(0.2)

            camera.stop_recording()
            if (stream_video):
                camera.stop_recording(splitter_port=2)

def set_camera_properties():
    
    global camera_view
    global picam_annotate_size
    global picam_text_background
    global picam_width
    global picam_height
    global picam_framerate
    global picam_quality 
    global video_directory
    
    
    if (camera_view == 'front'):
        picam_annotate_size = 17
        picam_text_background = "None"
        picam_width = 640
        picam_height = 360
        picam_framerate = 24
        picam_quality = 25
        video_directory = data_directory + '/front/'
    elif (camera_view == 'rear'):
        picam_annotate_size = 17
        picam_text_background = "None"
        picam_width = 640
        picam_height = 360
        picam_framerate = 24
        picam_quality = 25
        video_directory = data_directory + '/rear/'
    elif (camera_view == 'left'):
        picam_annotate_size = 50
        picam_text_background = "None"
        picam_width = 1920
        picam_height = 1080
        picam_framerate = 30
        picam_quality = 25
        video_directory = data_directory + '/left/'
    else:
        camera_view = 'left'
        picam_annotate_size = 50
        picam_text_background = "None"
        picam_width = 1920
        picam_height = 1080
        picam_framerate = 30
        picam_quality = 25
        video_directory = data_directory + '/left/'
    
#
#  Main
#

def main(argv):

    global camera_view
    global picam_annotate_size
    global picam_text_background
    global picam_width
    global picam_height
    global picam_framerate
    global picam_quality 
    global video_directory
    global display
    global stream_video
    global log
    global set_vflip
    global set_hflip

    display = 'full'
    stream_video = False
    camera_view = 'left'
    set_vflip = False
    set_hflip = False
    
    try:
      opts, args = getopt.getopt(argv,"hv:d:s",["help", "view=", "display=", "stream", "vflip", "hflip"])
    except getopt.GetoptError:
      print ('camera.py -v <camera_view> -d <display> -s')
      sys.exit(2)
      
    for opt, arg in opts:
      if opt == '-h':
         print ('camera.py -v <camera_view> -d <display> -s')
         sys.exit()
      elif opt in ("-v", "--view"):
         camera_view = arg
      elif opt in ("-d", "--display"):
         display = arg
      elif opt in ("-s", "--stream"):
         stream_video = True
      elif opt in ("--vflip"):
         set_vflip = True
      elif opt in ("--hflip"):
         set_hflip = True

    log = open(logfile_out, "a", 1) # non blocking
    time.sleep(video_delay)

    set_camera_properties()
    start_camera()

    sys.exit(0)

if __name__ == "__main__":
   main(sys.argv[1:])
