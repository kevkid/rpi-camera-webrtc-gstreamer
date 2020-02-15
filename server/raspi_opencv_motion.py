# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import cv2
import imutils
import datetime
from imutils.video import VideoStream
import time
from threading import Thread
import copy
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gst, GstBase, Gtk, GObject
import multiprocessing
import time
import os

class Monitor:
    def __init__(self, ipAddr, port, directory, threshold = 0.05, timeToRecord = 30, bitrate=512):
        self.keyFrame = None
        self.count = 0
        self.slidingWindow = []
        self.startRecord = False
        self.t_start = None
        self.t_end = None
        self.thresh = threshold
        self.timeToRecord = timeToRecord#Amount of time to record in seconds
        self.ipAddr = ipAddr
        self.port = port
        self.cap = cv2.VideoCapture('udpsrc auto-multicast=true port='+self.port+' caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtpjitterbuffer ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink sync=false', cv2.CAP_GSTREAMER)
        self.setKeyFrame = 60
        self.bitrate = str(bitrate)
        self.directory = directory
        self.frames = []
        Gst.init(None)
        if not os.path.exists(directory):#check for directory
            os.makedirs(directory)

    def play(self):
        #self.pipeline.send_event(Gst.Event.new_flush_start())
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.set_state(Gst.State.PLAYING)
    def stop(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.send_event(Gst.Event.new_eos())
        self.pipeline.set_state(Gst.State.NULL)
    def run(self):
        while(True):
        #capture frames and apply some blurs to later check absolute value
            ret, frame = self.cap.read()
            frame_rsz = imutils.resize(frame, width=300)#calculate on a small frame
            gray = cv2.cvtColor(frame_rsz, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            #if this is the begining of a stream set the keyframe to the first frame
            if self.keyFrame is None:
                self.keyFrame = gray
            # compute the absolute difference between the current frame and
            frameDelta = cv2.absdiff(self.keyFrame, gray)
            self.slidingWindow.append(np.average(frameDelta))

            if np.average(self.slidingWindow)/255 > self.thresh:#detect movement
                self.startRecord = True
                print('Started Recording')
                self.t_start = time.time()#update everytime there is motion
                timeStr = str(time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime()))

            if self.startRecord == True:
                self.frames.append(frame)#append frames
            if self.t_start and self.timeToRecord <= int((time.time()-self.t_start) % 60):#curr time - time started is larger than allotted time, if yes stop recording
                self.startRecord = False#stops recording
                print('Stopped Recording')
                pathOut = self.directory+'/'+timeStr+'.mkv'
                fps = 30
                size = np.shape(frame)[:2]
                out = cv2.VideoWriter(pathOut,cv2.VideoWriter_fourcc(*'H264'), fps, (size[1], size[0]))
                print('Saving to disk')
                for frame in self.frames:
                    # writing to a image array
                    out.write(frame)
                out.release()
                print('Finished Saving')
                self.frames = []
                self.t_start = None

            if self.count == self.setKeyFrame:
                #reset keyframe after x frames
                self.keyFrame = gray
                self.count = 0
                print('keyframe set!')
            del self.slidingWindow[0]
            self.count += 1
            #print("looped")



if __name__ == "__main__":
    cameraMonitor = Monitor(ipAddr='127.0.0.1', port='5000', threshold=0.05, timeToRecord=30, bitrate=2048)
    cameraMonitor.run()
