# coding: utf8
# !/usr/bin/env python3

import RPi.GPIO as gpio
<<<<<<< HEAD
import datetime
=======
>>>>>>> tmp
import time
import logging
import os

<<<<<<< HEAD
from gpiozero import PWMOutputDevice

dir_path = os.path.dirname(os.path.realpath(__file__))

TIME_UP = 5
TIME_DOWN = 6
=======
dir_path = os.path.dirname(os.path.realpath(__file__))

TIME_UP = 15
TIME_DOWN = 16
>>>>>>> tmp
FILENAME = os.path.join(dir_path, "status.txt")
LOGFILE = os.path.join(dir_path, "chicken.log")
# ///////////////// Define Motor Driver GPIO Pins /////////////////
# Motor A, Left Side GPIO CONSTANTS
PWM_FORWARD_LEFT_PIN = 13  # IN1 - Forward Drive
<<<<<<< HEAD
PWM_REVERSE_LEFT_PIN = 6  # IN2 - Reverse Drive

#
# forwardLeft = PWMOutputDevice(PWM_FORWARD_LEFT_PIN, True, 0, 1000)
# reverseLeft = PWMOutputDevice(PWM_REVERSE_LEFT_PIN, True, 0, 1000)
class ChickenDoor():
    
    def __init__(self):
        gpio.setmode(gpio.BCM)
        gpio.setwarnings(False)
        gpio.setup(PWM_FORWARD_LEFT_PIN, gpio.OUT)
        gpio.setup(PWM_REVERSE_LEFT_PIN, gpio.OUT)
        logging.basicConfig(filename="chicken.log", level=logging.DEBUG,
                            format="%(asctime)s — %(name)s — %(levelname)s — %(message)s")

    @staticmethod
    def read_status():
        file = open(FILENAME, "r")
        status = file.readline()
        print(status)
        file.close()
        return (status)
    
    @staticmethod
    def write_status(STATUS):
        file = open(FILENAME, "w")
        file.write(STATUS)
        file.close()
    
    
    def open_door(self):
        if self.read_status() == "Closed":
            print("Status = closed")
            logging.info("DOOR Opening…")
            self.open()
            logging.info("DOOR Opened !")
            self.write_status("Opened")
        else:
            logging.warning("ERROR! Action OPEN but door not closed!")

    def close_door(self):
        if self.read_status() == "Opened":
            self.write_status("Closing")
            logging.info("DOOR Closing…")
            self.close()
            logging.info("DOOR Closed!")
            self.write_status("Closed")
        else:
            logging.warning("ERROR! Action CLOSE but door not opened!")


    def force_open_door(self):
        logging.info("DOOR FORCED Opening…")
        self.open()
        logging.info("DOOR FORCED Opened!")
        self.write_status("Opened")


    def force_close_door(self):
        self.write_status("Closing")
        logging.info("DOOR FORCED Closing…")
        self.close()
        logging.info("DOOR FORCED Closed!")
        self.write_status("Closed")
    
    def open(self):
        self.write_status("Opening")
        self.send_command(gpio.HIGH, gpio.LOW)
        time.sleep(TIME_UP)

    def close(self):
        self.write_status("Opening")
        self.send_command(gpio.LOW, gpio.HIGH)
        time.sleep(TIME_DOWN)

    @staticmethod
    def send_command( c1, c2):
        gpio.output(PWM_FORWARD_LEFT_PIN, c1)
        gpio.output(PWM_REVERSE_LEFT_PIN, c2)
    
    def exit_door(self):
        gpio.cleanup()
=======
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
>>>>>>> tmp
