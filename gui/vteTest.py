#!/usr/bin/python3

import sys
import time
import signal
import datetime as dt

from vteControl import VTEControl

class vteTest():

    def __init__(self):

        print ("Initializaing vteTest")

        self.vte = VTEControl()

        self.lastStatus = dt.datetime.now()
        self.timestamp  = dt.datetime.now()

    def getWatchDog(self):

        print ("Getting WatchDog Information")
        
        systemData = self.vte.getServerURL()

        strTime = systemData['timestamp']

        print ("The timestamp on the Watchdog Information is " + strTime)

        self.timestamp = dt.datetime.strptime(systemData['timestamp'], '%Y-%m-%d %H:%M:%S')

        print ("Timestamp has been converted " + str(self.timestamp))

        if (self.timestamp > self.lastStatus):
            print ("Timestamp is later than when things started")
        elif (self.timestamp <= self.lastStatus):
            print ("Timestamp is earlier than when things started")

class Test():

    print ("Starting Test")
    
    test = vteTest()

    try:
        while True:
            test.getWatchDog()
            time.sleep(10)

    except (KeyboardInterrupt, SystemExit):
        print ("Exiting main function")
        sys.exit(0)

