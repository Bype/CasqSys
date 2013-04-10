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
        RPIO.setmode(RPIO.BCM)
        RPIO.setup(17, RPIO.IN, pull_up_down=RPIO.PUD_UP)
        RPIO.add_interrupt_callback(17, self.gpio_callback, edge='rising', debounce_timeout_ms=5000)
        RPIO.wait_for_interrupts(threaded=True)
        
    def gpio_callback(self, gpio_id, val):
        self.lock.acquire()
        self.isChangedAsked = True
        self.isTimedOut = False
        self.lock.release()      
        
    def startPlayer(self):
        tmpdir = tempfile.mkdtemp()
        filename = os.path.join(tmpdir, 'fifo.mjpeg')
        try:
            os.mkfifo(filename)
        except e:
            print ("Failed to create FIFO: %s" % e)
        cmd = ['omxplayer', '-r', filename]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, bufsize=0, stderr=subprocess.STDOUT)
        self.fifo = open(filename, 'w')
        
    def body_callback(self, buf):
        self.fifo.write(buf)
        self.lock.acquire()
        if(self.localtimeout < (datetime.datetime.now() - self.lastChange).seconds):
            self.isTimedOut = True
            if (self.currentHost != 'localhost'):
                aChangedAsked = True
        else:
            aChangedAsked = self.isChangedAsked
        self.lock.release()    
        if(aChangedAsked):
            return -1 
        

    def connectTo(self, host):
        self.lock.acquire()
        self.isChangedAsked = False
        if(self.isTimedOut):
            host = 'localhost'
        self.isTimedOut = False
        self.lastChange = datetime.datetime.now();
        self.currentHost = host
        self.lock.release()
        print 'connecting to ' + host
        self.connection = pycurl.Curl()
        self.connection.setopt(self.connection.URL, 'http://%s/?action=stream' % (host))
        self.connection.setopt(self.connection.BUFFERSIZE, 32768)
        self.connection.setopt(self.connection.WRITEFUNCTION, self.body_callback)
        
    def setupRedis(self):
        self.red = redis.StrictRedis(host='localhost', port=6379, db=0)
        
    def switchStream(self):
        try:
            self.connectTo(random.sample(red.smembers('ip'), 1))
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
                self.connection.close()
                self.switchStream()
            
if __name__ == "__main__":
    Player(60).main()

