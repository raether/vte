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

GPSD_PORT = 2947
GPSD_HOST = "127.0.0.1"
GPSD_PROTOCOL = 'json'
GPSD_VERSION = "0.27"
GPS_device = "/dev/ttyUSB1"
GPS_speed = "mph"
speed_unit = 3.6
GPS_wait = "yes"
previous_speed = 0.2

main_directory = "/home/camera"
usb_directory = main_directory + "/usb"
log_directory = main_directory + "/logs"
logfile_out = log_directory + "/status.log"

picam_use_usb = "no"
picam_time = 900
picam_annotate_size = 35
picam_text_background = "None"
picam_width = 1920
picam_height = 1080
picam_framerate = 30
picam_quality = 25
video_delay = 5

time.sleep(2)

#################################################################################################################
class GPSDSocket(object):

    def __init__(self, host=GPSD_HOST, port=GPSD_PORT, gpsd_protocol=GPSD_PROTOCOL, devicepath=None, verbose=False):

        self.devicepath_alternate = devicepath
        self.response = None
        self.protocol = gpsd_protocol  # What form of data to retrieve from gpsd  TODO: can it handle multiple?
        self.streamSock = None  # Existential
        self.verbose = verbose

        if host:
            self.connect(host, port)  # No host/port will fail here

#################
    def signal_handler(signal, frame):
        camera.stop_recording()
        log_data = dt.datetime.now().strftime('%T [picam]: Stopped recording\n')
        log.write(log_data)
        log.close()

        subprocess.call("printf 'picam closed' >> /tmp/dash_fifo &", shell=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)

#################
    def connect(self, host, port):
        """Connect to a host on a given port. """

        for alotta_stuff in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            family, socktype, proto, _canonname, host_port = alotta_stuff
            try:
                self.streamSock = socket.socket(family, socktype, proto)
                self.streamSock.connect(host_port)
                #self.streamSock.setblocking(False)
                self.streamSock.setblocking(True)

            finally:
               self.watch(gpsd_protocol=self.protocol)

#################
    def watch(self, enable=True, gpsd_protocol='json', devicepath=None):
        command = '?WATCH={{"enable":true,"{0}":true}}'.format(gpsd_protocol)
        if gpsd_protocol == 'human':  # human is the only imitation protocol
            command = command.replace('human', 'json')
        return self.send(command)

#################
    def send(self, commands):
        if sys.version_info[0] < 3:  # Not less than 3, but 'broken hearted' because
            self.streamSock.send(commands)  # 2.7 chokes on 'bytes' and 'encoding='
        else:
            self.streamSock.send(bytes(commands, encoding='utf-8'))  # It craps out here when there is no daemon running

#################
    def __iter__(self):
        return self

#################
    def next(self, timeout=0):
        try:
            (waitin, _waitout, _waiterror) = select.select((self.streamSock,), (), (), timeout)
            if not waitin:
                return
            else:
                gpsd_response = self.streamSock.makefile()  # was '.makefile(buffering=4096)' In strictly Python3
                self.response = gpsd_response.readline()  # When does this fail?

            return self.response  # No, seriously; when does this fail?

        except OSError as error:
            sys.stderr.write('The readline OSError in GPSDSocket.next is this: ', error)
            return  # TODO: means to recover from error, except it is an error of unknown etiology or frequency. Good luck.

    __next__ = next  # Workaround for changes in iterating between Python 2.7 and 3.4

#################
    def close(self):
        if self.streamSock:
            self.watch(enable=False)
            self.streamSock.close()
        self.streamSock = None
        return

#################################################################################################################

class Fix(object):

    def __init__(self):
        """Sets of potential data packages from a device through gpsd, as generator of class attribute dictionaries"""
        version = {"release",
                   "proto_major", "proto_minor",
                   "remote",
                   "rev"}

        tpv = {"alt",
               "climb",
               "device",
               "epc", "epd", "eps", "ept",
               "epv", "epx", "epy",
               "lat", "lon",
               "mode",
               "tag",
               "time",
               "track",
               "speed"}

        sky = {"satellites",
               "gdop", "hdop", "pdop", "tdop",
               "vdop", "xdop", "ydop"}

        gst = {"alt",
               "device",
               "lat", "lon",
               "major", "minor",
               "orient"
               "rms",
               "time"}

        att = {"acc_len", "acc_x", "acc_y", "acc_z",
               "depth",
               "device",
               "dip",
               "gyro_x", "gyro_y",
               "heading",
               "mag_len", "mag_st", "mag_x", "mag_y", "mag_z",
               "pitch", "pitch_st",
               "roll", "roll_st",
               "temperature",
               "time",
               "yaw", "yaw_st"}  # TODO: Check Device flags

        pps = {"device",
               "clock_sec", "clock_nsec",
               "real_sec", "real_nsec"}

        device = {"activated",
                  "bps",
                  "cycle", "mincycle",
                  "driver",
                  "flags",
                  "native",
                  "parity",
                  "path",
                  "stopbits",
                  "subtype"}  # TODO: Check Device flags

        poll = {"active",
                "fixes",
                "skyviews",
                "time"}

        devices = {"devices",
                   "remote"}

        error = {"message"}

        # The thought was a quick repository for stripped down versions, to add/subtract' module data packets'
        packages = {"VERSION": version,
                    "TPV": tpv,
                    "SKY": sky,
                    "ERROR": error}  # "DEVICES": devices, "GST": gst, etc.
        # TODO: Create the full suite of possible JSON objects and a better way for deal with subsets
        for package_name, datalist in packages.items():
            #_emptydict = {key: 'n/a' for (key) in datalist}  # There is a case for using None instead of 'n/a'
            _emptydict = {key: '' for (key) in datalist}  # There is a case for using None instead of 'n/a'
            setattr(self, package_name, _emptydict)
        self.SKY['satellites'] = [{'PRN': 'n/a',
                                   'ss': 'n/a',
                                   'el': 'n/a',
                                   'az': 'n/a',
                                   'used': 'n/a'}]


#################
    def refresh(self, gpsd_data_package):
        try:  # 'class', a reserved word is popped to allow, if desired, 'setattr(package_name, key, a_package[key])'
            fresh_data = json.loads(gpsd_data_package)  # error is named "ERROR" the same as the gpsd data package
            package_name = fresh_data.pop('class', 'ERROR')  # If error, return 'ERROR' except if it happened, it
            package = getattr(self, package_name, package_name)  # should have been too broken to get to this point.
            for key in package.keys():  # Iterate attribute package  TODO: It craps out here when device disappears
                #package[key] = fresh_data.get(key, 'n/a')  # that is, update it, and if key is absent in the socket
                package[key] = fresh_data.get(key, '')  # that is, update it, and if key is absent in the socket
                # response, present --> "key: 'n/a'" instead.'
        except AttributeError:  # 'str' object has no attribute 'keys'  TODO: if returning 'None' is a good idea
             # print("No Data")  # This is frequently indicative of the device falling out of the system
             return None
        except (ValueError, KeyError) as error:  # This should not happen, most likely why it's an exception.  But, it
	    #  THIS IS HAPPENING ALL THE TIME
            sys.stderr.write('There was a Value/KeyError at GPSDSocket.refresh: ', error,
                             '\nThis should never happen.')  # happened once.  But I've no idea aside from it broke.

            return None

#################
    def satellites_used(self):  # Should this be ancillary to this class, or even included?
        total_satellites = 0
        used_satellites = 0
        for satellites in self.SKY['satellites']:
            if satellites['used'] is 'n/a':
                return 0, 0
            used = satellites['used']
            total_satellites += 1
            if used:
                used_satellites += 1

        return total_satellites, used_satellites

#################
    def make_datetime(self):  # Should this be ancillary to this class, or even included?

        timeformat = '%Y-%m-%dT%H:%M:%S.000Z'  # ISO8601
        if 'n/a' not in self.TPV['time']:
            gps_datetime_object = datetime.strptime(self.TPV['time'], timeformat).replace(
                tzinfo=(timezone(timedelta(0))))
        else:
            gps_datetime_object = datetime.strptime('1582-10-04T12:00:00.000Z', timeformat).replace(
                tzinfo=(timezone(timedelta(0))))
        return gps_datetime_object

#################
if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()  # TODO: beautify and idiot-proof makeover to prevent clash from options error
    # Defaults from the command line
    parser.add_argument('-human', dest='gpsd_protocol', const='human', action='store_const', default='human', help='DEFAULT Human Friendlier ')
    # parser.add_argument('-host', action='store', dest='host', default='127.0.0.1', help='DEFAULT "127.0.0.1"')
    # parser.add_argument('-port', action='store', dest='port', default='2947', help='DEFAULT 2947', type=int)
    # parser.add_argument("-verbose", action="store_true", default=False, help="increases verbosity, but not that much")
    # Alternate devicepath
    # parser.add_argument('-device', dest='devicepath', action='store', help='alternate devicepath e.g.,"/dev/ttyUSB4"')
    parser.add_argument('-json', dest='gpsd_protocol', const='json', action='store_const', help='/* output as JSON objects */')

    args = parser.parse_args()
    # session = GPSDSocket(args.host, args.port, args.gpsd_protocol, args.devicepath,
    #                      args.verbose)  # the historical 'session'

    session = GPSDSocket(GPSD_HOST,GPSD_PORT, 'human', 'None', 'False')
    fix = Fix()

#################################################################################################################
#
#  This function defines the text that is overlayed on the video

def gps_annotate():

        #time.sleep(0.1)  # to keep from spinning silly, or set GPSDSocket.streamSock.setblocking(False) to True

        for socket_response in session:
	    #
	    #  Output for humans because it is the command line
	    #
            if socket_response and args.gpsd_protocol is 'human':
               fix.refresh(socket_response)

               speed_ms = '{speed:0<5}'.format(**fix.TPV)

               if speed_ms in ['00000']:
                  current_speed = "0.0"
               else:
                  speed_cv = float(speed_ms)
                  current_speed = speed_cv * speed_unit
                  global previous_speed
                  previous_speed = current_speed
            else:
               current_speed = previous_speed # previous is better than none

            lat_float = "{lat:0<11}".format(**fix.TPV)
            lon_float = "{lon:0<12}".format(**fix.TPV)

            gps_text = " VS: {0:<3.0f} ".format(float(current_speed)) + \
                       "  Lat: {0:2.6f} ".format(float(lat_float)) + \
                       "  Long: {0:2.6f} ".format(float(lon_float))

            break
        return gps_text

def radar_annotate():
    
    r = requests.get('http://localhost:8080')
    data = json.loads(r.text)
    patrol_speed = str(data["PatrolSpeed"])
    locked_target = str(data["LockedTarget"])
    target_speed = str(data["TargetSpeed"])
    gps_text = gps_annotate();

    current_time = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    radar_text = " Front Camera    " + current_time + "       " + \
                 " T: " + target_speed +  "  " + \
                 " L: " + locked_target + "  " + \
                 " P: " + patrol_speed +  "      " + \
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

    sequence_count = 1
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
    
        sequence_count += 1

sys.exit(0)
