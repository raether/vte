#! /usr/bin/python
 
import os
from gps import *
from time import *
import time
import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import json
from vtelog import vteLog

PORT_NUMBER = 9001

main_directory = "/home/camera/vte"
log_directory = main_directory + "/logs"
data_directory = main_directory + "/data"
gpslog_directory = data_directory + "/gps/"
logfile_out = log_directory + "/status.log"

gpsd = None   #seting the global variable

#This class will handles any incoming request from
#the browser

class gpsHandler(BaseHTTPRequestHandler):
	
    #Handler for the GET requests
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        # Send the json message
        message = json.dumps({
                        'Latitude'  : curr_lat,
                        'Longitude' : curr_long,
                        'Time'      : curr_time,
                        'Speed'     : curr_speed,
                        'Heading'   : curr_heading,
                        'ErrorEps'  : curr_eps,
                        'ErrorEpx'  : curr_epx,
                        'ErrorEpv'  : curr_epv,
                        'ErrorEpt'  : curr_ept
                        })
        self.wfile.write(message)
        return

    def log_message(self, format, *args):
        return

class GpsPoller(threading.Thread):
    
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
    self.daemon = True
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
 
if __name__ == '__main__':
  gpsp = GpsPoller()   # Create the GPS Poller Thread
  
  try:

        log = open(logfile_out, "a", 1) # non blocking

        gpslog = vteLog(gpslog_directory,'gps','csv')

        gpsp.start() # start it up

        #
        #  Start up simple HTTP Server to handle requests for radar information
        #
        server = HTTPServer(('', PORT_NUMBER), gpsHandler)

        t=threading.Thread(target=server.serve_forever)
        t.daemon = True
        t.start()

        print 'Started httpserver on port ' , PORT_NUMBER
        print "Reading Serial Port..."

        while True:
            curr_lat = gpsd.fix.latitude
            curr_long = gpsd.fix.longitude
            curr_time = gpsd.utc
            curr_eps = gpsd.fix.eps
            curr_epx = gpsd.fix.epx
            curr_epv = gpsd.fix.epv
            curr_ept = gpsd.fix.ept
            curr_speed = round(gpsd.fix.speed * 2.23694)
            curr_heading = gpsd.fix.track

            gpslog.write_log(str(curr_time) + ', '+ \
                             str(curr_lat) + ', ' + \
                             str(curr_long) + ', ' + \
                             str(curr_speed) + ', ' + \
                             str(curr_heading) + ', ' + \
                             str(curr_eps) + ', ' + \
                             str(curr_epx) + ', ' + \
                             str(curr_epv) + ', ' + \
                             str(curr_ept) + '\n')
     
            time.sleep(1) #set to whatever
 
  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "\nKilling Thread..."
    gpsp.running = False
    gpsp.join() # wait for the thread to finish what it's doing
  print "Done.\nExiting."

