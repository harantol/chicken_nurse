#!/usr/bin/env python

from picamera import PiCamera
from time import sleep
import tensorflow as tf
import tflite_runtime.interpreter as tflite

camera = PiCamera()
camera.start_preview()
sleep(5)
camera.capture('./tmp_picture.jpg')
camera.stop_preview()


interpreter = tf.lite.Interpreter(model_path=args.model_file)
