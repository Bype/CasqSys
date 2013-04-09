#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
# vi:ts=4:et
# $Id: basicfirst.py,v 1.5 2005/02/11 11:09:11 mfx Exp $

import sys
import pycurl
import subprocess
import os, tempfile
import datetime
import RPIO
from time import sleep
from thread import allocate_lock

RPIO.setmode(RPIO.BCM)
RPIO.setup(17, RPIO.IN, pull_up_down=RPIO.PUD_UP)


tmpdir = tempfile.mkdtemp()
filename = os.path.join(tmpdir, 'fifo.mjpeg')
print (filename)
try:
    os.mkfifo(filename)
except e:
    print ("Failed to create FIFO: %s" % e)

cmd = ['omxplayer', '-r', filename]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE,bufsize=0, stderr=subprocess.STDOUT)
f = open(filename,'w')
st = False
lock = allocate_lock()

def body_callback(buf):
    f.write(buf)
    lock.acquire()
    mySt = st
    lock.release()
    if(mySt):
        return -1
   

def gpio_callback(gpio_id, val):
    print("gpio %s: %s" % (gpio_id, val))
    lock.acquire()
    global st 
    st = True
    lock.release()      

RPIO.add_interrupt_callback(17, gpio_callback, edge='rising', debounce_timeout_ms=100)
RPIO.wait_for_interrupts(threaded=True)


while(True):
    print "Starting..."
    lock.acquire()
    st=False
    lock.release()
    c = pycurl.Curl()
    c.setopt(c.URL, 'http://192.168.2.195/?action=stream')
    c.setopt(c.BUFFERSIZE,32768)
    c.setopt(c.WRITEFUNCTION, body_callback)
    try:
        c.perform()
    except:
        c.close()
        print "Changing Stream"
        sleep(5)
        print "Again ?"
        
        

