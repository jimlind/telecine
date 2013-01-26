#!/usr/bin/python
# -*- coding: utf-8 -*-

from ctypes import sizeof as ctypesizeof
from ctypes import c_voidp as ctypevoid
from datetime import *
from os import open as osopen
from os import O_RDONLY as osreadonly
from os import read as osread
from re import search
from struct import pack as structpack
from struct import unpack_from as structunpack
from subprocess import call
from subprocess import CalledProcessError as callerror
from subprocess import check_output as callout

'''
import os
import subprocess
import struct
import sys
import time
import locale
import ctypes
'''

'''
Get mouse name
$ xinput list | grep "slave  pointer"

Get camera id
$ ls /dev/v4l/by-id/
 '''
mouse_name = 'PS/2+USB Mouse'
camera_path = '/dev/v4l/by-id/usb-046d_0821_FE3FA0E0-video-index0'

''' Detect architecture for InputEvent '''
__voidptrsize = ctypesizeof(ctypevoid)
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
            self.time, n0, self.nanotime, n1, n2, self.etype, self.evalue = structunpack(INPUTEVENT_STRUCT, buf)
        elif _32bit:
            self.time, self.nanotime, n0, self.etype, self.evalue = structunpack(INPUTEVENT_STRUCT, buf)
        return self
    def pack(self):
        if _64bit:
            return structpack(INPUTEVENT_STRUCT, self.time, 0, self.nanotime, 0, self.etype, self.evalue)
        elif _32bit:
            return structpack(INPUTEVENT_STRUCT, self.time, self.nanotime, self.etype, self.evalue)
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
        output = callout(["file", "-b",string])
    except callerror as e:
        return False

    results = search("symbolic link .+/(.+)'", output)
    if results:
	return results.group(1)
    else:
        return False

''' Recieves InputEvents from the buffer ''' 
def receive(event, video_id):
    if event.etype == 272 and event.evalue == 0:
	print "Let's Go!"	
'''
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
'''

''' Get the party started '''
if __name__ == '__main__':
    video_id = find_video_binding(camera_path)
    if video_id:
        video_settings = {
            "Brightness": "128",
            "Contrast": "32",
            "Saturation": "32",
            "White Balance Temperature, Auto": "0",
            "Gain": "76",
            "Power Line Frequency": "2",
            "White Balance Temperature": "3504",
            "Sharpness": "72",
            "Backlight Compensation": "0",
            "Exposure (Absolute)": "664",
            "Exposure, Auto Priority": "0",
            "Focus (absolute)": "0",
            "Focus, Auto": "0",
            "Zoom, Absolute": "1",
        }
        for key, value in video_settings.iteritems():
            call(["uvcdynctrl", "-d", video_id, "-s", key, value])

    mouse_event = find_event_id(mouse_name) 
    if mouse_event:
        device = "/dev/input/" + mouse_event
        fileno = osopen(device, osreadonly)
        buf = ""
        while True:
           buf += osread(fileno, 4096)
           while len(buf) >= INPUTEVENT_STRUCT_SIZE:
               receive(InputEvent(buf[:INPUTEVENT_STRUCT_SIZE]), video_id)
               buf = buf[INPUTEVENT_STRUCT_SIZE:]
    else:
        print "Something is rotten in the state of Denmark."
