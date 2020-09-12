#!/usr/bin/env python

from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.start_preview()
sleep(5)
camera.capture('./tmp_picture.jpg')
camera.stop_preview()