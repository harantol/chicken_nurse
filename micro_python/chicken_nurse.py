import datetime
from datetime import date

from sun import Sun

from machine import Pin
import time

LATITUDE = 45.343167
LONGITUDE = 5.586088
TIME_ZONE = 2
OFFSET_SEC = 1800  # seconds

TIME_UP = 30  # seconds
TIME_DOWN = 30  # seconds
FILENAME = "status.txt"
LOGFILE = "chicken.log"
# ///////////////// Define Motor Driver GPIO Pins /////////////////
# Motor A, Left Side GPIO CONSTANTS
PWM_FORWARD_LEFT_PIN = 15  # IN1 - Forward Drive
PWM_REVERSE_LEFT_PIN = 14  # IN2 - Reverse Drive

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
    stop()
    p0.close()
    p1.close()


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


class ChickenNurse:
    def __init__(self, debug=False, use_deep_sleep=True):
        self.lat = LATITUDE
        self.lon = LONGITUDE
        self.time_zone = TIME_ZONE
        self.sun_wait = Sun(lat=self.lat, lon=self.lon, tzone=self.time_zone)
        self.MODES = ['Fermeture', 'Ouverture']
        self.debug_flag = True
        self.use_deep_sleep = use_deep_sleep
        self.debug = debug
        if self.debug:
            print("DEBUG")
            self.offset_sec = 5  # 1800
        else:
            self.offset_sec = OFFSET_SEC
        self.led = Pin("LED", Pin.OUT)
        self.led.off()

    def get_next_step_and_time(self, loc_time=None):

        if loc_time is None:
            cur_time_tuple = time.localtime()
        else:
            cur_time_tuple = loc_time
        cur_time = time.mktime(cur_time_tuple)
        sunrise_time = time.mktime(self.sun_wait.get_sunrise_time(cur_time_tuple) + (0, 0, 0))
        sunset_time = time.mktime(self.sun_wait.get_sunset_time(cur_time_tuple) + (0, 0, 0))

        if cur_time - sunrise_time < 0:  # Avant le lever du soleil
            sleeptime = sunrise_time - self.offset_sec - cur_time
            print(f"{sleeptime}s avant le lever du soleil")
            mode = self.MODES[1]
            # Lever de demain
        elif (cur_time - sunset_time) < 0:  # Avant le coucher du soleil
            sleeptime = sunset_time + self.offset_sec - cur_time
            print(f"{sleeptime}s avant le coucher du soleil")
            mode = self.MODES[0]
        else:  # Après le coucher du soleil
            tomorrow = date.fromtimestamp(cur_time) + datetime.timedelta(days=1)
            sunrise_time = time.mktime(self.sun_wait.get_sunrise_time(tomorrow.tuple() + (0, 0)) + (0, 0, 0))
            sleeptime = sunrise_time - self.offset_sec - cur_time
            print(f"{sleeptime}s après le coucher du soleil")
            mode = self.MODES[1]
        if sleeptime < 0:
            raise ValueError("Sleep time is < 0 !")
        return sleeptime, mode

    def get_next_step_and_time_debug(self):
        self.debug_flag = ~self.debug_flag
        return 3, self.MODES[self.debug_flag]

    def toggle_chicken_nurse(self, mode):
        self.led.on()
        if mode == self.MODES[0]:
            close_door()
        elif mode == self.MODES[1]:
            open_door()
        self.led.off()

    def run(self):
        while True:
            loc = time.localtime()
            # loc = (2023, 12, 31, 21, 34, 0, 5, 273)
            print(f"il est {loc}, la porte est {read_status()}")
            if self.debug:
                sleeptime, mode = self.get_next_step_and_time_debug()
            else:
                sleeptime, mode = self.get_next_step_and_time(loc_time=loc)
            print(f"Prochaine {mode} à {time.gmtime(sleeptime + time.mktime(loc))} dodo pendant {sleeptime}s")
            if self.use_deep_sleep:
                picosleep.seconds(sleeptime)
            else:
                time.sleep(sleeptime)
            print(f"C'est l'heure ! {mode} à {time.localtime()}")
            self.toggle_chicken_nurse(mode)
            if self.use_deep_sleep:
                picosleep.seconds(int(2 * self.offset_sec))
            else:
                time.sleep(int(2 * self.offset_sec))
