import time
from machine import Pin

TIME_UP = 30  # seconds
TIME_DOWN = 30  # seconds
FILENAME = "door_state.txt"
# ///////////////// Define Motor Driver GPIO Pins /////////////////
# Motor A, Left Side GPIO CONSTANTS
PWM_FORWARD_LEFT_PIN = 15  # IN1 - Forward Drive
PWM_REVERSE_LEFT_PIN = 14  # IN2 - Reverse Drive
STATUS_CLOSED = "Closed"
STATUS_OPENED = "Opened"
STATUS_CLOSING = "Closing"
STATUS_OPENING = "Opening"
STATUS_NO_FILE = "No file"

p0 = Pin(PWM_FORWARD_LEFT_PIN, Pin.OUT)
p1 = Pin(PWM_REVERSE_LEFT_PIN, Pin.OUT)


def open_door():
    if read_status() != STATUS_OPENED:
        print("Opening because door is " + read_status())
        opening()
        print("Status = " + read_status())
    else:
        print("Door is already " + STATUS_OPENED)


def close_door():
    if read_status() != STATUS_CLOSED:
        print("Closing because door is " + read_status())
        closing()
        print("Status = " + read_status())
    else:
        print("Door is already " + STATUS_CLOSED)


def force_open_door():
    opening()


def force_close_door():
    closing()


def opening():
    write_status(STATUS_OPENING)
    p0.high()
    p1.low()
    time.sleep(TIME_UP)
    stop()
    write_status(STATUS_OPENED)


def closing():
    write_status(STATUS_CLOSING)
    p0.low()
    p1.high()
    time.sleep(TIME_DOWN)
    stop()
    write_status(STATUS_CLOSED)


def stop():
    p0.low()
    p1.low()


def write_status(status):
    with open(FILENAME, "w") as file:
        file.write(status)


def read_status():
    try:
        with open(FILENAME, "r") as file:
            status = file.readline()
    except OSError:
        status = 'NO FILE'
    return status
