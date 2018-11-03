#!/usr/bin/python3

import datetime
import time
import os

#
#  This class maintains a file for logging data.  It will rotate the file based on the number
#  of minutes specified in timeBoundary.  For examle, timeBoundary = 5, will rotate the file
#  every 5 minutes.
#
#  Class variables for creation of the log object:
#      path = directory path where to store the log files.
#
#      name = prefix of the log file name.
#
#      suffix = suffix of the log file name (type of file).  For example "csv" for a comma
#               separated file.
#
#      timeBoundary = the number of minutes before the file gets rotated.  Valid values are 0-59
#                    A value of zero means to never rotate.
#
#   Log files get created with the name in the format of:
#       <name> _ <YYYYMMDD> _ <hhmmss> . <prefix>
#
#   The first log file timestamp will get labeled with the time of the first write entry.
#   Subsequent log file timestamps will get labeled with the time stamp boundary.

#   Example - assuming a 5 minute log boundary where the first log entry gets written at 09:12:34am
#   on January 23, 2018
#
#      First log file name will have a timestamp  - 20180123_091234
#      Second log file name will have a timestamp - 20180123_091500
#      Third log file name will have a timestamp  - 20180123_092099
#

class vteLog:

    def __init__(self, path, name, suffix, timeBoundary):
        self.path         = path
        self.name         = name
        self.suffix       = suffix
        self.timeBoundary = timeBoundary
        self.firstWrite   = False
        self.firstMinutes = int(datetime.datetime.now().minute)
        self.firstSeconds = int(datetime.datetime.now().second)
        self.lastRotate   = self.firstMinutes
        self.currentFile  = ""
        self.baseFile     = self.path + name + '.' + suffix

        #
        #  TODO:  Check to make sure the path name has a "/" at the end.
        #  If it doesn't add the slash.
        #

    def getFilename(self, minString, secString):
        #
        #  Expect that minString and secString are string values for minutes and seconds of
        #  log file.
        #
        logTimeStamp = datetime.datetime.now().strftime('%Y%m%d_%H')
        logFilename = self.name + "_" + logTimeStamp + minString + secString + "." + self.suffix
        return logFilename

    def rotate(self):
        minString = self.boundaryMinutesLabel()
        secString = '00'
        self.currentFile = self.getFilename(minString, secString)
        self.lastRotate  = int(minString)

    def setFirst(self):
        minString = datetime.datetime.now().strftime('%M')
        secString = datetime.datetime.now().strftime('%S')
        self.firstWrite = True
        self.currentFile = self.getFilename(minString, secString)
        self.lastRotate  = int(minString)

    def writeLog(self, message):

        if (self.firstWrite == False):
            self.setFirst()
        else:
            if self.readyToRotate():
                self.rotate()         
                if os.path.exists(self.baseFile):
                    os.remove(self.baseFile)

        logfile = self.path + self.currentFile

        #
        #  Make the directory if it does not exist
        #
        if not os.path.exists(self.path):
            os.makedirs(self.path)
   
        self.open_file = open(logfile,'a',1) # non blocking
        self.open_file.write(message)
        self.open_file.close()
        
        self.open_file = open(self.baseFile,'a',1) # non blocking
        self.open_file.write(message)
        self.open_file.close()

    def boundaryCheck(self):
        
        currentMinutes = int(datetime.datetime.now().minute)

        # Checks if we are at a multiple of time boundary minutes

        if (not(currentMinutes % self.timeBoundary)):
            return True
        else:
            return False

    def boundaryMinutesLabel(self):
        currentMinutes = int(datetime.datetime.now().minute)
        minOffset      = currentMinutes % self.timeBoundary
        minLabel       = currentMinutes - minOffset

        if (minLabel < 10):
            return ('0' + str(minLabel))
        else:
            return (str(minLabel))
    
    def readyToRotate(self):

        #
        #  Never rotate if timeBoundary == 0
        #
        if (self.timeBoundary == 0):
            return False

        currentMinutes = int(datetime.datetime.now().minute)

        # Checks if we are at a multiple of time boundary minutes and if our current minutes don't
        # equal our last rotation

        if (not(currentMinutes % self.timeBoundary)  and  currentMinutes != self.lastRotate):
            return True
        else:
            return False

#
#  Test of package
#

def main():
    print ("Log Tester")
    mylog = vteLog('/home/camera/vte/data/test/', 'test', 'csv', 5)
    i = 1
    while True:
        mylog.writeLog("Hello World " + str(i) + '\n')
        print ("Current File : ", mylog.currentFile)
        i = i+1
        time.sleep(10)
        
if __name__ == "__main__":
    main()

                                                         
