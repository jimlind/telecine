#!/usr/bin/python
# -*- coding: utf-8 -*-
from subprocess import call
from subprocess import CalledProcessError as callerror
from subprocess import check_output as callout
from subprocess import PIPE as pipe

import decimal
import glob
import re
import serial
import subprocess
import time

'''
Since I use an external USB webcam I just plug and unplug after running
the commands to identify the device

Get camera_path
$ ls /dev/v4l/by-id/
 '''
camera_path = '/dev/v4l/by-id/usb-046d_0821_FE3FA0E0-video-index0'
arduino_path = '/dev/ttyACM0'

max_diff = 1400000
video_id = None
video_path = None
arduino = None



''' Finds the bound ID for the V4L device '''
def find_video_binding(string):
    try:
        output = callout(["file", "-b", string])
    except callerror as e:
        return False
    
    results = re.search("symbolic link .+/(.+)'", output)
    if results:
        return results.group(1)
    else:
        return False



''' This happens with the switch is triggered '''
def triggerEvent():
    timestamp = str(int(time.time()))
    
    ''' Pause the motor '''
    arduino.write('P')
    
    ''' Reseting focus is needed before every shot '''
    call(["uvcdynctrl", "-d", video_id, "-s", "Focus (absolute)", "0"])
    call(["uvcdynctrl", "-d", video_id, "-s", "Focus (absolute)", "153"])
    
    ''' Take the picture '''
    call(["guvcview", "-s", "2048x1536", "-i", "frames/c.jpg", \
            "-m", "1", "-c", "1", "-d", video_path, \
            "--exit_on_close", "--no_display"], stdout=pipe, stderr=pipe)
    
    ''' Find file '''
    filename = "frames/c-1.jpg"
    files = glob.glob("frames/c*.jpg")
    if files:
        filename = files[0]
    
    ''' Rename file '''
    newfile = "frames/" + timestamp + ".jpg"
    call(["mv", filename, newfile])
    call(["chmod", "777", newfile])
    print "Wrote " + newfile
    
    ''' Check if the captured frame is blank '''
    out = subprocess.check_output(["compare", "-metric", "AE", \
            "blank.jpg", newfile, "/dev/null"], stderr=subprocess.STDOUT)
    pixel_diff = decimal.Decimal(out.strip())
    if pixel_diff < max_diff:
        print "Detected Blank Frame"
        arduino.write('E')
        return False
    
    ''' Resume the motor '''
    arduino.write('R')



''' Initialization of System '''
def initialize():
    global video_id
    global video_path
    global arduino
    
    call(["mkdir", "frames"], stdout=pipe, stderr=pipe)
    call(["chmod", "777", "frames"], stdout=pipe, stderr=pipe)
    
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
            "Exposure, Auto": "1",
            "Exposure (Absolute)": "664",
            "Exposure, Auto Priority": "0",
            "Focus, Auto": "0",
            "Zoom, Absolute": "1",
        }
        for key, value in video_settings.iteritems():
            call(["uvcdynctrl", "-d", video_id, "-s", key, value])
    else :
        print "Video input not found"
    
    video_path = "/dev/" + video_id
    arduino = serial.Serial(arduino_path, 9600)



''' Get the party started '''
initialize()

while True:
    arduino_input = arduino.read().strip()
    if arduino_input == "T":
        triggerEvent()


