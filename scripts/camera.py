#!/usr/bin/python3
#

from __future__ import print_function
from datetime import datetime, timedelta, timezone

import picamera
from picamera import Color
import datetime as dt

import sys
import signal
import os.path

import socket
import select
import time
import json
import requests

import subprocess

main_directory = "/home/camera"
log_directory = main_directory + "/logs"
logfile_out = log_directory + "/status.log"

picam_time = 900
picam_annotate_size = 35
picam_text_background = "None"
picam_width = 1920
picam_height = 1080
picam_framerate = 30
picam_quality = 25
video_delay = 5

#################################################################################################################
#
#  This function defines the text that is overlayed on the video

def gps_annotate():
    
    try:
        r = requests.get('http://localhost:9001')
        if r.status_code == 200:
            try:
                data = json.loads(r.text)
                lat_float = data["Latitude"]
                lon_float = data["Longitude"]
                current_speed = data["Speed"]
                heading = data["Heading"]
            except Exception as e:
                print (e)  
        else:
            gps_text = "NO GPS DATA"
            return gps_text
    except:
        gps_text = "NO GPS DATA"
        return gps_text

    gps_text = " VS: {0:<3.0f}".format(float(current_speed)) + \
               " Head: {0:<3.0f}".format(float(heading)) + \
               "  Lat: {0:2.6f} ".format(float(lat_float)) + \
               "Long: {0:2.6f} ".format(float(lon_float))

    return gps_text

def radar_annotate():

    try:
        r = requests.get('http://localhost:8080')
        if r.status_code == 200:
            data = json.loads(r.text)
            patrol_speed = str(data["PatrolSpeed"])
            locked_target = str(data["LockedTarget"])
            target_speed = str(data["TargetSpeed"])
        else:
            radar_text = "NO RADAR DATA"
            return radar_text
    except:
        radar_text = "NO RADAR DATA"
        return radar_text
    
    gps_text = gps_annotate();

    current_time = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    radar_text = " Front Camera  " + current_time + "   " + \
                 " T: " + target_speed +  "  " + \
                 " L: " + locked_target + "  " + \
                 " P: " + patrol_speed +  "   " + \
                 gps_text + " "

    return radar_text

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
                 

#################################################################################################################
#   MAIN
#################################################################################################################


log = open(logfile_out, "a", 1) # non blocking

time.sleep(video_delay)

with picamera.PiCamera() as camera:

    #
    #  set camera properties
    #
    camera.resolution = (picam_width, picam_height)
    camera.framerate = picam_framerate
    # camera.vflip = True
    # camera.hflip = True
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
    # myvlc = subprocess.Popen(cmdline, stdin=subprocess.PIPE)

    #
    #  Main loop for recording video
    #
    while True:
    
        video_file = log_directory + "/front/" + dt.datetime.now().strftime('%Y%m%d_%H%M.h264')
        last_rotate = dt.datetime.now().strftime('%M')
        log_data = dt.datetime.now().strftime('%T [picam]: ') + "Started recording " + video_file + "\n"
        log.write(log_data)
        #
        #  Set the preview screen location on the HDMI Display
        #
        camera.start_preview(fullscreen=False, window = (0, 38, 960, 540))
        #
        #  Start recording the video based on the camera properties
        #
        camera.start_recording(video_file, quality=picam_quality, format='h264')
        #
        #  Start a h.264 stream to the http port
        #
        # camera.start_recording(myvlc.stdin, format='h264', splitter_port=2)
    
        start = dt.datetime.now()
        #
        #  Record video only for the picam_time duration.  Then start a new file.
        #
        while not ready_to_rotate(last_rotate):   
            camera.annotate_text = radar_annotate()
            camera.wait_recording(0.2)

        camera.stop_recording()
        # camera.stop_recording(splitter_port=2)

sys.exit(0)
