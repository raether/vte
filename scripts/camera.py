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

main_directory = "/home/camera/vte"
log_directory = main_directory + "/logs"
data_directory = main_directory + "/data"
logfile_out = log_directory + "/status.log"

video_delay = 1
camera_view = "back"    # Valid views are front, back, and left

if (camera_view == 'front'):
    picam_annotate_size = 35
    picam_text_background = "None"
    picam_width = 1920
    picam_height = 1080
    picam_framerate = 30
    picam_quality = 25
    video_directory = data_directory + '/front/'
elif (camera_view == 'back'):
    picam_annotate_size = 19
    picam_text_background = "None"
    picam_width = 960
    picam_height = 540
    picam_framerate = 30
    picam_quality = 25
    video_directory = data_directory + '/back/'
elif (camera_view == 'left'):
    picam_annotate_size = 35
    picam_text_background = "None"
    picam_width = 1920
    picam_height = 1080
    picam_framerate = 30
    picam_quality = 25
    video_directory = data_directory + '/left/'
else:
    picam_annotate_size = 35
    picam_text_background = "None"
    picam_width = 1920
    picam_height = 1080
    picam_framerate = 30
    picam_quality = 25
    video_directory = data_directory + '/front/'
    
#################################################################################################################
#
#  These functions defines the text that is overlayed on the video

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
            radar_text = "NO RADAR DATA    "
            return radar_text
    except:
        radar_text = "NO RADAR DATA    "
        return radar_text

    radar_text = " T: " + target_speed +  "  " + \
                 " L: " + locked_target + "  " + \
                 " P: " + patrol_speed +  "   "

    return radar_text

def vte_annotate():

    current_time = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if (camera_view == "front"):
        gps_text = gps_annotate()
        radar_text = radar_annotate()
        camera_annotate = " Front Camera  " + current_time + "   " + radar_text + gps_text + " "
    elif (camera_view == "back"):
        camera_annotate = " Back Camera  " + current_time
    elif (camera_view == "left"):
        camera_annotate = " Left Camera  " + current_time
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
    if (camera_view == 'back'):
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
        camera.start_preview(fullscreen=False, window = (0, 38, 960, 540))
        #
        #  Start recording the video based on the camera properties
        #
        camera.start_recording(video_file, quality=picam_quality, format='h264')
        #
        #  Start a h.264 stream to the http port
        #
        if (camera_view == 'back'):
            camera.start_recording(myvlc.stdin, format='h264', splitter_port=2)
    
        start = dt.datetime.now()
        #
        #  Record video only for the picam_time duration.  Then start a new file.
        #
        while not ready_to_rotate(last_rotate):   
            camera.annotate_text = vte_annotate()
            camera.wait_recording(0.2)

        camera.stop_recording()
        if (camera_view == 'back'):
            camera.stop_recording(splitter_port=2)

sys.exit(0)
