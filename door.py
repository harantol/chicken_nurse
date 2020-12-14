# coding: utf8
# !/usr/bin/env python3

import RPi.GPIO as gpio
import datetime
import time
import logging
import os

from gpiozero import PWMOutputDevice

dir_path = os.path.dirname(os.path.realpath(__file__))

TIME_UP = 45
TIME_DOWN = 38
FILENAME = os.path.join(dir_path, "status.txt")
LOGFILE = os.path.join(dir_path, "chicken.log")
# ///////////////// Define Motor Driver GPIO Pins /////////////////
# Motor A, Left Side GPIO CONSTANTS
PWM_FORWARD_LEFT_PIN = 13  # IN1 - Forward Drive
PWM_REVERSE_LEFT_PIN = 6  # IN2 - Reverse Drive

#
# forwardLeft = PWMOutputDevice(PWM_FORWARD_LEFT_PIN, True, 0, 1000)
# reverseLeft = PWMOutputDevice(PWM_REVERSE_LEFT_PIN, True, 0, 1000)

def init():
    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)
    gpio.setup(PWM_FORWARD_LEFT_PIN, gpio.OUT)
    gpio.setup(PWM_REVERSE_LEFT_PIN, gpio.OUT)
    logging.basicConfig(filename="chicken.log", level=logging.DEBUG,
                        format="%(asctime)s — %(name)s — %(levelname)s — %(message)s")


def read_status():
    file = open(FILENAME, "r")
    status = file.readline()
    print(status)
    file.close()
    return (status)


def write_status(STATUS):
    file = open(FILENAME, "w")
    file.write(STATUS)
    file.close()


def open_door():
    print(read_status())
    if read_status() == "Closed":
        write_status("Opening")
        logging.info("DOOR Opening…")
        gpio.output(PWM_FORWARD_LEFT_PIN, gpio.HIGH)
        gpio.output(PWM_REVERSE_LEFT_PIN, gpio.LOW)
        # forwardLeft.value = 1.0
        # reverseLeft.value = 0
        time.sleep(TIME_UP)
        logging.info("DOOR Opened !")
        write_status("Opened")
    else:
        logging.warning("ERROR! Action OPEN but door not closed!")


def force_open_door():
    write_status("Opening")
    logging.info("DOOR FORCED Opening…")
    gpio.output(PWM_FORWARD_LEFT_PIN, gpio.HIGH)
    gpio.output(PWM_REVERSE_LEFT_PIN, gpio.LOW)
    time.sleep(TIME_UP)
    logging.info("DOOR FORCED Opened!")
    write_status("Opened")


def close_door():
    print(read_status())
    if read_status() == "Opened":
        write_status("Closing")
        logging.info("DOOR Closing…")
        gpio.output(PWM_FORWARD_LEFT_PIN, gpio.LOW)
        gpio.output(PWM_REVERSE_LEFT_PIN, gpio.HIGH)
        time.sleep(TIME_DOWN)
        logging.info("DOOR Closed!")
        write_status("Closed")
    else:
        logging.warning("ERROR! Action CLOSE but door not opened!")


def force_close_door():
    write_status("Closing")
    logging.info("DOOR FORCED Closing…")
    gpio.output(PWM_FORWARD_LEFT_PIN, gpio.LOW)
    gpio.output(PWM_REVERSE_LEFT_PIN, gpio.HIGH)
    time.sleep(TIME_DOWN)
    logging.info("DOOR FORCED Closed!")
    write_status("Closed")


def exit_door():
    gpio.cleanup()
