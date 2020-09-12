# coding: utf8
# !/usr/bin/env python3

import RPi.GPIO as gpio
import time
import logging
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

TIME_UP = 15
TIME_DOWN = 16
FILENAME = os.path.join(dir_path, "status.txt")
LOGFILE = os.path.join(dir_path, "chicken.log")
# ///////////////// Define Motor Driver GPIO Pins /////////////////
# Motor A, Left Side GPIO CONSTANTS
PWM_FORWARD_LEFT_PIN = 13  # IN1 - Forward Drive
PWM_REVERSE_LEFT_PIN = 26  # IN2 - Reverse Drive

def init():
    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)
    gpio.setup(PWM_FORWARD_LEFT_PIN, gpio.OUT)
    gpio.setup(PWM_REVERSE_LEFT_PIN, gpio.OUT)
    logging.basicConfig(filename="chicken.log", level=logging.DEBUG,
                        format="%(asctime)s — %(name)s — %(levelname)s — %(message)s")


def open_door():
    if read_status() == "Closed" or read_status() == "Opening" :
        print("Status = closed")
        logging.info("DOOR Opening…")
        opening()
        logging.info("DOOR Opened !")
        write_status("Opened")
    else:
        logging.warning("ERROR! Action OPEN but door not closed!")


def close_door():
    if read_status() == "Opened" or read_status() == "Closing":
        print("Status = Opened")
        logging.info("DOOR Closing…")
        closing()
        logging.info("DOOR Closed!")
        write_status("Closed")
    else:
        logging.warning("ERROR! Action CLOSE but door not opened!")


def force_open_door():
    logging.info("DOOR FORCED Opening…")
    opening()
    logging.info("DOOR FORCED Opened!")
    write_status("Opened")


def force_close_door():
    write_status("Closing")
    logging.info("DOOR FORCED Closing…")
    closing()
    logging.info("DOOR FORCED Closed!")
    write_status("Closed")



def opening():
    write_status("Opening")
    send_command(gpio.HIGH, gpio.LOW)
    time.sleep(TIME_UP)


def closing():
    write_status("Closing")
    send_command(gpio.LOW, gpio.HIGH)
    time.sleep(TIME_DOWN)


def exit_door():
    gpio.cleanup()


def write_status(status):
    with open(FILENAME, "w") as file:
        file.write(status)


def read_status():
    with open(FILENAME, "r") as file:
        status = file.readline()
        print(status)
    return status


def send_command(c1, c2):
    gpio.output(PWM_FORWARD_LEFT_PIN, c1)
    gpio.output(PWM_REVERSE_LEFT_PIN, c2)
