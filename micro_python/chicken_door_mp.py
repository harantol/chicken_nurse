# coding: utf8
# !/usr/bin/env python3
from machine import Pin
import time

TIME_UP = 30
TIME_DOWN = 25
FILENAME = "status.txt"
LOGFILE = "chicken.log"
# ///////////////// Define Motor Driver GPIO Pins /////////////////
# Motor A, Left Side GPIO CONSTANTS
PWM_FORWARD_LEFT_PIN = 14  # IN1 - Forward Drive
PWM_REVERSE_LEFT_PIN = 15  # IN2 - Reverse Drive

STATUS_CLOSED = "Closed"
STATUS_OPENED = "Opened"
STATUS_CLOSING = "Closing"
STATUS_OPENING = "Opening"

p0 = Pin(PWM_FORWARD_LEFT_PIN, Pin.OUT)
p1 = Pin(PWM_REVERSE_LEFT_PIN, Pin.OUT)


def open_door():
    if read_status() == STATUS_CLOSED or read_status() == STATUS_OPENING:
        print("Status = " + STATUS_CLOSED)
        opening()
        write_status(STATUS_OPENED)
    print("Status = " + STATUS_OPENED)


def close_door():
    if read_status() == STATUS_OPENED or read_status() == STATUS_CLOSING:
        print("Status = " + STATUS_OPENED)
        closing()
        write_status(STATUS_CLOSED)
    print("Status = " + STATUS_CLOSED)


def force_open_door():
    write_status(STATUS_OPENING)
    opening()
    write_status(STATUS_OPENED)


def force_close_door():
    write_status(STATUS_CLOSING)
    closing()
    write_status(STATUS_CLOSED)


def opening():
    write_status(STATUS_OPENING)
    p0.high()
    p1.low()
    time.sleep(TIME_UP)
    stop()


def closing():
    write_status(STATUS_CLOSING)
    p0.low()
    p1.high()
    time.sleep(TIME_DOWN)
    stop()


def stop():
    p0.low()
    p1.low()


def exit_door():
    Pin.cleanup()


def write_status(status):
    with open(FILENAME, "w") as file:
        file.write(status)


def read_status():
    with open(FILENAME, "r") as file:
        status = file.readline()
    return status
