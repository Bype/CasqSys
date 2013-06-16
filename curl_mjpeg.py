#! /usr/bin/env python

import sys
import pycurl
import subprocess
import os, tempfile
import datetime
import RPIO
import redis
import random
from time import sleep
from thread import allocate_lock

class Player(object):
    def __init__(self, timeo):
        self.lock = allocate_lock()
        self.isChangedAsked = False
        self.isTimedOut = False 
        self.lastChange = datetime.datetime.now();
        self.localtimeout = timeo
        self.currentHost = 'localhost'
        
    def setupRPIO(self):
        # Button event detection on release
        RPIO.setmode(RPIO.BCM)
        RPIO.setup(17, RPIO.IN, pull_up_down=RPIO.PUD_UP)
        RPIO.add_interrupt_callback(17, self.gpio_callback, edge='rising', debounce_timeout_ms=1000)
        # wait 1 second between to event
        RPIO.wait_for_interrupts(threaded=True)
        
    def gpio_callback(self, gpio_id, val):
        # Button released
        self.lock.acquire()
        # thread safe access
        self.isChangedAsked = True
        # set to switch 
        self.isTimedOut = False
        # but not to local
        self.lock.release()      
        
    def startPlayer(self):
        # create a temp file
        tmpdir = tempfile.mkdtemp()
        filename = os.path.join(tmpdir, 'fifo.mjpeg')
        try:
            # create a fifo file
            os.mkfifo(filename)
        except e:
            print ("Failed to create FIFO: %s" % e)
        cmd = ['omxplayer', '-r', filename]
        # launching player with pipe
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, bufsize=0, stderr=subprocess.STDOUT)
        self.fifo = open(filename, 'w')
        
    def body_callback(self, buf):
        # http packet callback
        if(99 < sys.getsizeof(buf)):
        # small packet is http header no need to bother player with that 
             self.fifo.write(buf)
        aChangedAsked = False
        # local variable
        self.lock.acquire()
        # thread safe section
        if(self.isChangedAsked):
            aChangedAsked = True
        else:
            if(self.localtimeout < (datetime.datetime.now() - self.lastChange).seconds):
                # time check
                self.isTimedOut = True
                if (self.currentHost != 'localhost'):
                    # change only if not already on local channel
                    aChangedAsked = True
        self.lock.release()    
        if(aChangedAsked):
            # ask for disconnecting http client
            return -1 
        

    def connectTo(self, host):
        self.lock.acquire()
        # thread safe
        self.isChangedAsked = False
        if(self.isTimedOut):
            host = 'localhost'
        self.isTimedOut = False
        self.lastChange = datetime.datetime.now();
        # new timer start 
        self.currentHost = host
        self.lock.release()
        print 'connecting to ' + host
        self.connection = pycurl.Curl()
        # initiate http connection
        self.connection.setopt(self.connection.URL, 'http://%s/?action=stream' % (host))
        self.connection.setopt(self.connection.BUFFERSIZE, 262144)
        # get anything you can usually a complete mjpeg block
        self.connection.setopt(self.connection.WRITEFUNCTION, self.body_callback)
        
    def setupRedis(self):
        # just connect to redis server
        self.red = redis.StrictRedis(host='localhost', port=6379, db=0)
        
    def switchStream(self):
        # choose a random server
        try:
            newHost = random.sample(self.red.smembers('ip'), 1)[0]
            if(self.currentHost != newHost):
                # if it's a different host than current connect to it 
                self.connectTo(newHost)
            else:
                # if not get back to local so user feel something change push the button
                self.connectTo('localhost')
        except:
            self.connectTo('localhost')

    def main(self):
        self.setupRPIO()
        self.setupRedis()
        self.startPlayer()
        self.connectTo('localhost')
        while(True):
            try:
                self.connection.perform()
            except:
                # when callback return is <0 an exception is raiser
                # this mean connection need to be closed an reconnect elsewhere
                self.connection.close()
                self.switchStream()
            
if __name__ == "__main__":
    Player(7).main()
    # 7 second is timeout to local

