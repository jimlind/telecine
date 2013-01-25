#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import *
from subprocess import call
import os
import subprocess
import struct
import sys
import time
import locale
import ctypes

''' Define the X11 mouse ID and mouse name here
use command :  
$ xinput list | grep "slave  pointer" 
 '''
device_name = 'PS/2+USB Mouse'
xinput_id = "14"


''' Map a mouse boutton to a external sensor (label) '''
mouse_key_dic = {
	272: "Stock",   # Left button
	273: "Stock 2" ,  # Right button
	274: "Stock 3"  , # middle button
} 

''' Map mouse buttons events '''
mouse_event_dic = {
	0: "open", # button release => Door Opened
	1: "close", # button press => Door closed
} 

__voidptrsize = ctypes.sizeof(ctypes.c_voidp)
_64bit = (__voidptrsize == 8)
_32bit = (__voidptrsize == 4)
if _64bit:
    INPUTEVENT_STRUCT = "=LLLLHHl"
    INPUTEVENT_STRUCT_SIZE = 24
elif _32bit: # 32bit
    INPUTEVENT_STRUCT = "=iiHHi"
    INPUTEVENT_STRUCT_SIZE = 16
else:
    raise RuntimeError("Couldn't determine architecture, modify " + __file__ +
                       " to support your system.")

def detect_mouse(name):
    fd = file("/proc/bus/input/devices")
    entry = {}
    mouse = None

    for line in fd:
        line = line.strip()
        if not line and entry:
            if entry['N'] == 'Name="'+name+'"':
                ev = None
                ismouse = False
                for h in entry['H'].split(' '):
                    if 'mouse' in h:
                        ismouse = True
                    if 'event' in h:
                        ev = h
                if ismouse:
                    mouse = ev

        elif line:
            l, r = line.split(":", 1)
            r = r.strip()
            entry[l] = r
    return mouse


''' Class from https://github.com/rmt/pyinputevent '''
class InputEvent(object):
    """
    A `struct input_event`. You can instantiate it with a buffer, in which
    case the method `unpack(buf)` will be called.  Or you can create an
    instance with `InputEvent.new(type, code, value, timestamp=None)`, which
    can then be packed into the structure with the `pack` method.
    """
    __slots__ = ('etype', 'ecode', 'evalue', 'time', 'nanotime')

    def __init__(self, buf=None):
        """By default, unpack from a buffer"""
        if buf:
            self.unpack(buf)

    def set(self, etype, ecode, evalue, timestamp=None):
        """Set the parameters of this InputEvent"""
        if timestamp is None:
            timestamp = time.time()
        self.time, self.nanotime = int(timestamp), int(timestamp%1*1000000.0)
        self.etype = etype
        self.ecode = ecode
        self.evalue = evalue
        return self

    @classmethod
    def new(cls, etype, ecode, evalue, time=None):
        """Construct a new InputEvent object"""
        e = cls()
        e.set(etype, ecode, evalue, time)
        return e

    @property
    def timestamp(self):
        return self.time + (self.nanotime / 1000000.0)

    def unpack(self, buf):
        if _64bit:
            self.time, t1, self.nanotime, t3, \
            self.etype, self.ecode, self.evalue \
            = struct.unpack_from(INPUTEVENT_STRUCT, buf)
        elif _32bit:
            self.time, self.nanotime, self.etype, \
            self.ecode, self.evalue \
            = struct.unpack_from(INPUTEVENT_STRUCT, buf)
        return self
    def pack(self):
        if _64bit:
            return struct.pack(INPUTEVENT_STRUCT, 
            self.time, 0, self.nanotime, 0,
            self.etype, self.ecode, self.evalue)
        elif _32bit:
            return struct.pack(INPUTEVENT_STRUCT, 
            self.time, self.nanotime,
            self.etype, self.ecode, self.evalue)
    def __repr__(self):
        return "<InputEvent type=%r, code=%r, value=%r>" % \
            (self.etype, self.ecode, self.evalue)
    def __str__(self):
        return "type=%r, code=%r, value=%r" % \
            (self.etype, self.ecode, self.evalue)
    def __hash__(self):
        return hash( (self.etype, self.ecode, self.evalue,) )
    def __eq__(self, other):
        return self.etype == other.etype \
            and self.ecode == other.ecode \
            and self.evalue == other.evalue

def receive(event):
    if event.etype == 1 and event.evalue == 0:
	print "Reset UVC Controls"
	call(["uvcdynctrl", "-d", "video1", "-L", "/home/jlind/8mm/settings/reset.txt"])
	print "Set UVC Controls"	
	call(["uvcdynctrl", "-d", "video1", "-L", "/home/jlind/8mm/settings/controls.txt"])

	print "Capturing..."
	image_prefix = "/home/jlind/8mm/cap-" + str(int(time.time()))
	print image_prefix
	call(["guvcview", "-s", "2048x1536", "-i", image_prefix + ".jpg", \
		"-m", "1", "-c", "1", "-d", "/dev/video1", \
		"--exit_on_close", "--no_display"], \
 		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	call(["chown", "jlind", image_prefix + "-1.jpg"])
	call(["chmod", "777", image_prefix + "-1.jpg"])

if __name__ == '__main__':
	''' '''
	'''
	print "Reset UVC Controls"
	call(["uvcdynctrl", "-d", "video1", "-L", "/home/jlind/8mm/settings/reset.txt"])
	print "Set UVC Controls"	
	call(["uvcdynctrl", "-d", "video1", "-L", "/home/jlind/8mm/settings/controls.txt"])
	'''

	event_name = detect_mouse(device_name)
	 
	if event_name != None: 
		device = "/dev/input/" + event_name
		print "Mouse found ! Use event file %s" % device
		''' Disable mouse from X11 '''
	 	os.system('xinput set-int-prop '+ xinput_id + ' "Device Enabled" 8 0' )
	
		''' '''
		fileno = os.open(device, os.O_RDONLY)
		buf = ""
		"""
		Read up to 4096 bytes from the input device, and generate an
		InputEvent for every 24 (or 16) bytes (sizeof(struct input_event))
		"""
		while True:
			buf += os.read(fileno, 4096)
			while len(buf) >= INPUTEVENT_STRUCT_SIZE:
				receive(InputEvent(buf[:INPUTEVENT_STRUCT_SIZE]))
				buf = buf[INPUTEVENT_STRUCT_SIZE:]

	else:
		print "Unable to find defined mouse. Bye."

	print "reset"
	call(["uvcdynctrl", "uvcdynctrl -d video1 -L /home/jlind/8mm/settings/reset.txt"])
	print "controls"	
	call(["uvcdynctrl", "uvcdynctrl -d video1 -L /home/jlind/8mm/settings/controls.txt"])

