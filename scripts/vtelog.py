#!/usr/bin/python

import datetime
import time

class vteLog:

    def __init__(self, path, name, suffix):
        self.path = path
        self.name = name
        self.suffix = suffix
        self.last_rotate_string = datetime.datetime.now().strftime('%M')
        self.last_rotate = int(self.last_rotate_string)
        if (0 <= self.last_rotate <= 14):
            self.last_rotate = 0
        elif 15 <= (self.last_rotate <= 29):
            self.last_rotate = 15
        elif (30 <= self.last_rotate <= 44):
            self.last_rotate = 30
        elif (45 <= self.last_rotate <= 59):
            self.last_rotate = 45
        else:
            self.last_rotate = 0
        self.current_file = self.get_path() + self.get_name()
            
    def get_path(self):
        return self.path

    def get_name(self):
        log_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H') + \
                                                         self.last_rotate_string
        log_filename = self.name + '_' + log_timestamp + "." + self.suffix
        return log_filename

    def get_current_file(self):
        return self.current_file

    def rotate(self):
        current_min = int(datetime.datetime.now().strftime('%M'))
                                
        if 0 <= current_min <= 14 and self.last_rotate != 0:
            self.last_rotate        = 0
            self.last_rotate_string = '00'
        elif 15 <= current_min <= 29 and self.last_rotate != 15:
            self.last_rotate        = 15
            self.last_rotate_string = '15'                                                        
        elif 30 <= current_min <= 44 and self.last_rotate != 30:
            self.last_rotate        = 30
            self.last_rotate_string = '30'
        elif 45 <= current_min <= 59 and self.last_rotate != 45:
            self.last_rotate        = 45
            self.last_rotate_string = '45'

    def ready_to_rotate(self) :
                                                         
        current_min = int(datetime.datetime.now().strftime('%M'))
                                
        if 0 <= current_min <= 14 and self.last_rotate != 0:
            return True
        elif 15 <= current_min <= 29 and self.last_rotate != 15:
            return True                                                       
        elif 30 <= current_min <= 44 and self.last_rotate != 30:
            return True
        elif 45 <= current_min <= 59 and self.last_rotate != 45:
            return True
        else:
            return False

    def write_log(self, message):

        if self.ready_to_rotate():
            self.rotate()
            self.current_file = self.get_path() + self.get_name()
            
        self.open_file = open(self.current_file,'a',1) # non blocking
        self.open_file.write(message)
        self.open_file.close()
      

def main():
    print ("Log Tester")
    mylog = vteLog('/home/camera/vte/data/front/', 'front', 'h264')
    i = 1
    while True:
        mylog.write_log("Hello World " + str(i) + '\n')
        i = i+1
        time.sleep(10)

        
if __name__ == "__main__":
    main()

                                                         
