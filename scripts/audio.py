#!/usr/bin/python3
#
##import datetime
##import datetime as dt

##from __future__ import print_function
import os
import sys
import signal
import time
import subprocess
import threading

import getopt
import argparse

from vtelog import vteLog

#
#  arecord is the shell command used to collect audio from a Bluetooth Microphone.
#  This seems to work fine with PulseAudio.  The default microphone is set via the
#  PulseAudio server.
#
#  Some options for a record are:
#   -q  --quiet          Quiet mode.  Suurpress messages
#   -t  --file-type      File type (voc, wav, raw or au).  If this parameter is ommitted
#                        the WAVE format is used.
#   -c  --channels       The number of channels.  The default is one channel.
#                        Valid values are 1 through 32
#
#   -f   --format        Sample format are: S8 U8 S16_LE S16_BE U16_LE U16_BE
#                        S24_LE S24_BE U24_LE U24_BE S32_LE S32_BE U32_LE U32_BE
#                        FLOAT_LE FLOAT_BE FLOAT64_LE FLOAT64_BE IEC958_SUBFRAME_LE
#                        IEC958_SUBFRAME_BE MU_LAW A_LAW IMA_ADPCM MPEG GSM SPECIAL
#                        S24_3LE S24_3BE U24_3LE U24_3BE S20_3LE S20_3BE U20_3LE
#                        U20_3BE S18_3LE S18_3BE U18_3LE
#
#                        The available format shortcuts are:
#                         -f cd (16 bit little endian, 44100, stereo) [-f S16_LE -c2 -r44100]
#                         -f cdr (16 bit big endian, 44100, stereo) [-f S16_BE -c2 -f44100]
#                         -f dat (16 bit little endian, 48000, stereo) [-f S16_LE -c2 -r48000]
#
#                        If no format is given U8 is used.
#
#   -r    --rate         Sampling rate in Hertz. The default rate is 8000 Hertz. If the value specified
#                        is less than 300, it is taken as the rate in kilohertz.
#                        Valid values are 2000 through 192000 Hertz.
#
#   -d, --duration       Interrupt after # seconds. A value of zero means infinity.
#                        The default is zero, so if this option is omitted then the arecord process
#                        will run until it is killed.
#
#    Signals             When recording, SIGINT, SIGTERM and SIGABRT will close the output file and exit.
#                        SIGUSR1 will close the output file, open a new one, and continue recording.
#                        However, SIGUSR1 does not work with --separate-channels.
#
#   https://linux.die.net/man/1/arecord
#

class VTEAudio():

    def __init__(self):

        self.args = None
        
        self.mainDirectory  = "/home/camera/vte"
        self.logDirectory   = self.mainDirectory + "/logs"
        self.dataDirectory  = self.mainDirectory + "/data"
        self.audioDirectory = self.dataDirectory + "/audio/"
        self.logFileOut     = self.logDirectory + "/status.log"
        
        self.audioDelay = 0.2
        self.quiet      = False
        self.debug      = False
        self.sampleRate = 16000
        self.channels   = 2

        self.audioLog = vteLog(self.audioDirectory, 'audio', 'wav')

    #
    #  This function allows input of properties via command line
    #

    def propertyInput(self, argv):

        self.args = argv
        
        try:
            opts, args = getopt.getopt(self.args, "ha:r:qd",
                                       ["help", "samplerate=", "audiodelay=", "quiet", "debug"])

        except getopt.GetoptError:
            print("audio.py -h    to get HELP on options")
            sys.exit(2) 
        
        for opt, arg in opts:
            if opt == '-h':
                print('audio.py options:')
                print('    -r    --samplerate   set sample rate')
                print('    -a    --audiodelay   set the number of seconds to wait for checking on')
                print('                         file rollover')
                print('    -q    --quiet        supress output from arecord')
                print('    -d    --debug        turn on debug mode')
                sys.exit()
            
            elif opt in ("-r", "--samplerate"):
                self.sampleRate = arg
            
            elif opt in ("-a", "--audiodelay"):
                self.audioDelay = arg
                
            elif opt in ("-q", "--quiet"):
                self.quiet = True

            elif opt in ("-d", "--debug"):
                self.debug = True

    #
    #  This function performs the audio record.
    #   1.  Figure out what the current audio file should be named
    #   2.  Record to the audio file.
    #

    def recordAudio(self):
    
        print ("Entering recordAudio function")
        
        #
        #  arecord -f S16_LE -c 2 -r 16000 a.wav
        #
        audioFile = self.audioLog.get_current_file()
        print ("Storing at ", audioFile)
        print ("Start Audio recording")

        cmdline = ['arecord', '-f', 'S16_LE', '-c', '2', '-r', '16000', audioFile]
        proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE )

        print ("Exiting recordAudio function")
        return proc

#
#  Main
#

def main(argv):
    print ("VTE Audio Starting...")

    #
    #  Create Audio object
    #

    vteaudio= VTEAudio()

    #
    #  Parse Arguments
    #
    vteaudio.propertyInput(argv)

    #
    #  Record Audio
    #

    proc = vteaudio.recordAudio()
    
    while True:
        try:
            #
            #  Check to see if we need to break file into 15 minute chunk
            #
            if (vteaudio.audioLog.ready_to_rotate()):
                #
                #  Stop current audio recording
                #
                proc.send_signal(signal.SIGTERM)
                print ("Stopping current recording")
                #
                #  Start new audio recording
                #
                vteaudio.audioLog.rotate()
                proc = vteaudio.recordAudio()
                print ("Starting new recording")

            time.sleep(vteaudio.audioDelay)

        #
        #  Handle Exit
        #
        
        except(KeyboardInterrupt, SystemExit):
            #
            #  Stop the current recording
            #
            proc.send_signal(signal.SIGTERM)
            print ("Stopping current recording")
            print ("VTE Audio Ending...")
            exit()

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
