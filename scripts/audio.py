#!/usr/bin/python3

import os
import sys
import signal
import os.path
import datetime as dt
import time
import argparse
import textwrap
import logging
import subprocess
import threading

from logging.handlers import TimedRotatingFileHandler

#
#  VTE Audio is a python wrapper around the linux command arecord.
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

#
#  Classs Description
#

class VTEAudio():

    #
    #  Initialize File Locations
    #
    mainDirectory    = "/home/camera/vte"
    logDirectory     = mainDirectory + "/logs"
    dataDirectory    = mainDirectory + "/data"
    subDataDirectory = dataDirectory + "/audio"
    dataFilePrefix   = "audio"
    dataFileSuffix   = "wav"
    logFileName      = logDirectory + "/status"

    gpsURL        = "http://control.local:9001"
    radarURL      = "http://control.local:9002"

    waitTime      = 0.2  # Real-time break for main loop
    timeBoundary  = 5    # Minute boundary to roll over information files


    def __init__(self, args):

        logger.debug ("Initializing VTE Audio Object")

        #
        #  Initialize Audio Object Parameters
        #
        self.quiet       = args.quiet
        self.debug       = args.debug
        self.sampleRate  = args.samplerate
        self.channels    = 2
        self.audioFormat = 'S16_LE'
        self.fileType    = VTEAudio.dataFileSuffix

        logger.debug(vars(self))
        logger.debug("Finished initialization")

    def recordAudio(self):
    
        logger.debug("Entering recordAudio function")
        
        #
        #  arecord -f S16_LE -c 2 -r 16000 a.wav
        #
        audioFormat = self.audioFormat
        channels    = str(self.channels)
        sampleRate  = str(self.sampleRate)
        audioFile   = self.dataFile
        
        logger.info ("Storing at " + audioFile)
        logger.info ("Start Audio recording")

        cmdline = ['arecord', '-f', audioFormat, '-c', channels, '-r', sampleRate, audioFile]
        logger.debug ("calling arecord as : " + str(cmdline))
        proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE )

        logger.debug ("Exiting recordAudio function")
        return proc

    def rotateCheck(self):

        currentMinutes = int(dt.datetime.now().minute)

            #   Checks if we are at a multiple of time boundary minutes and if our current minutes don't
            #       equal our last rotation

        if (not(currentMinutes % VTEAudio.timeBoundary)  and  currentMinutes != self.lastRotate):
            logger.debug ("Current Minutes = " + str(currentMinutes))
            logger.debug (vars(self))
            logger.debug ("Check for file rotation.  Rotate File")
            return True

        else:
            return False

    def setDataFile(self):

        logger.debug ("Setting the Data File Name")

        #
        #  Make the video directory if it does not exist
        #

        if not os.path.exists(VTEAudio.subDataDirectory):
            os.makedirs(VTEAudio.subDataDirectory)

        self.dataFile    = VTEAudio.subDataDirectory + '/' + \
                           VTEAudio.dataFilePrefix + "_" + dt.datetime.now().strftime('%Y%m%d_%H%M%S') + \
                             "." + VTEAudio.dataFileSuffix
        self.lastRotate  = int(dt.datetime.now().strftime('%M'))  # Set last rotation

        logger.debug ("Done Setting the Video File Name")

#########################################
#  Main
#########################################
def main(args):

    logger.debug ("Entering main function")

    vteaudio = VTEAudio(args)        # Create VTE Audio Object   

    try:
        #
        #  Main Loop for Program
        #

        while(True):
            #
            #  Set audio recording file and start audio recording
            #
            vteaudio.setDataFile()
            proc = vteaudio.recordAudio()
            
            while not (vteaudio.rotateCheck()):
                time.sleep(VTEAudio.waitTime)

            #
            #  Stop current audio recording
            #
            proc.send_signal(signal.SIGTERM)
            logger.info ("Stopping current audio recording")


    except (KeyboardInterrupt, SystemExit):
        logger.debug("Exiting main function")
        sys.exit(0)

if __name__ == "__main__":

    #
    #  Parse Command Line Options
    #

    
    parser = argparse.ArgumentParser(prog='audio.py',
                 formatter_class=argparse.RawDescriptionHelpFormatter,
                 description='Video Taffic Enforcement Audio - Version 0.1')

    parser.add_argument('-r', '--samplerate', default=8000, help="Set Sample Rate")
    parser.add_argument('-q', '--quiet', action='store_true', help="Surpress output from arecord")
    parser.add_argument('-v', '--debug', action='store_true',help="Turn on debug mode for logging")

    args = parser.parse_args()
    
    #
    #  Configure Logging
    #
    FORMAT  = 'Audio: %(asctime)-15s: %(levelname)-5s: %(message)s'
    logger  = logging.getLogger('status')
    handler = logging.handlers.TimedRotatingFileHandler(VTEAudio.logFileName, when='midnight')
    
    handler.setFormatter(logging.Formatter(FORMAT))

    if (args.debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.addHandler(handler)
                        
    logger.info ("Starting Audio")
    logger.debug (vars(args))
    
    #
    #  Start main with command-line arguments
    #
    main(args)
