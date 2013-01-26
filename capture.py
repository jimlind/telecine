#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import *
from subprocess import call
from re import search

import os
import subprocess
import struct
import sys
import time
import locale
import ctypes

'''
Get mouse name
$ xinput list | grep "slave  pointer"

Get camera id
$ ls /dev/v4l/by-id/
 '''
mouse_name = 'PS/2+USB Mouse'
camera_path = '/dev/v4l/by-id/usb-046d_0821_FE3FA0E0-video-index0'


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

''' Detect architecture for InputEvent '''
__voidptrsize = ctypes.sizeof(ctypes.c_voidp)
_64bit = (__voidptrsize == 8)
_32bit = (__voidptrsize == 4)
if _64bit:
    INPUTEVENT_STRUCT = "=LLLLHHl"
    INPUTEVENT_STRUCT_SIZE = 24
elif _32bit: # 32bit
    INPUTEVENT_STRUCT = "=iiHHi"
    INPUTEVENT_STRUCT_SIZE = 16

''' I don't understand what this is doing exactly. I trust it to work '''
class InputEvent(object):
    __slots__ = ('etype', 'evalue', 'time', 'nanotime')
    def __init__(self, buf=None):
        if buf:
            self.unpack(buf)
    def set(self, etype, evalue, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        self.time, self.nanotime = int(timestamp), int(timestamp%1*1000000.0)
        self.etype = etype
        self.evalue = evalue
        return self
    @classmethod
    def new(cls, etype, evalue, time=None):
        e = cls()
        e.set(etype, evalue, time)
        return e
    @property
    def timestamp(self):
        return self.time + (self.nanotime / 1000000.0)
    def unpack(self, buf):
        if _64bit:
            self.time, t1, self.nanotime, t3, self.etype, self.evalue = struct.unpack_from(INPUTEVENT_STRUCT, buf)
        elif _32bit:
            self.time, self.nanotime, self.etype, self.evalue = struct.unpack_from(INPUTEVENT_STRUCT, buf)
        return self
    def pack(self):
        if _64bit:
            return struct.pack(INPUTEVENT_STRUCT, self.time, 0, self.nanotime, 0, self.etype, self.evalue)
        elif _32bit:
            return struct.pack(INPUTEVENT_STRUCT, self.time, self.nanotime, self.etype, self.evalue)
    def __repr__(self):
        return "<InputEvent type=%r, value=%r>" % (self.etype, self.evalue)
    def __str__(self):
        return "type=%r, value=%r" % (self.etype, self.evalue)
    def __hash__(self):
        return hash((self.etype, self.evalue))
    def __eq__(self, other):
        return self.etype == other.etype and self.evalue == other.evalue
''' end class InputEvent '''



''' Finds the Event ID for the device name input '''
def find_event_id(name):
    devices = file("/proc/bus/input/devices")
    name_found = False

    for line in devices:
	line = line.strip()
	if not name_found and line == 'N: Name="'+name+'"':
            name_found = True
        if name_found and 'Handler' in line:
            for text in line.split(' '):
                if 'event' in text:
                    return text
    return False



''' Finds the bound ID for the V4L device '''
def find_video_binding(string):
    try:
        output = subprocess.check_output(["file", "-b",string])
    except subprocess.CalledProcessError as e:
        return False

    results = search("symbolic link .+/(.+)'", output)
    if results:
	return results.group(1)
    else:
        return False

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




''' Get the party started '''
if __name__ == '__main__':
    mouse_event = find_event_id(mouse_name)
    video_id = find_video_binding(camera_path)

    if mouse_event and video_id:
	print "Everything is shiney."
    else:
        print "Something is rotten in the state of Denmark."
"""
    

	mouse_event = find_event_id(mouse_name)
	print mouse_event	
	video_id = find_video_binding(camera_path)
	print video_id	 

	event_name = None

	if event_name != None: 
		device = "/dev/input/" + event_name
		print "Mouse found ! Use event file %s" % device
		''' Disable mouse from X11 '''
	 	os.system('xinput set-int-prop '+ xinput_id + ' "Device Enabled" 8 0' )
	
		''' '''
		fileno = os.open(device, os.O_RDONLY)
		buf = ""
		""
		Read up to 4096 bytes from the input device, and generate an
		InputEvent for every 24 (or 16) bytes (sizeof(struct input_event))
		""
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
"""
