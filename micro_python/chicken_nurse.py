import datetime
from datetime import date
import picosleep
from sun import Sun

from machine import Pin, RTC
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
        self.modes = ['Fermeture', 'Ouverture']
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
        self.log_txt = ""
        self.clock = RTC()

    def run(self):
        while True:
            if not self.debug:
                self.log_txt = ""
            loc = time.localtime()
            __text = f"Nous sommes le {self.__time_to_string(loc)}, la porte est {read_status()}\n"
            print(__text)
            self.log_txt += __text
            if self.debug:
                sleeptime, mode = self.__get_next_step_and_time_debug()
            else:
                sleeptime, mode = self.__get_next_step_and_time(loc_time=loc)
            __text = f"Prochaine {mode} le {self.__time_to_string(time.gmtime(sleeptime + time.mktime(loc)))}\n"
            print(__text)
            self.log_txt += __text
            self.__pause(sleeptime)
            __text = f"****************************\n C'est l'heure ! {mode} le {self.__time_to_string(time.localtime())}\n"
            print(__text)
            self.log_txt += __text
            self.__toggle_chicken_nurse(mode)
            self.__pause(int(2 * self.offset_sec))
            self.__write_log()

    def __get_next_step_and_time(self, loc_time=None):

        if loc_time is None:
            cur_time_tuple = time.localtime()
        else:
            cur_time_tuple = loc_time
        cur_time = time.mktime(cur_time_tuple)
        sunrise_time = time.mktime(self.sun_wait.get_sunrise_time(cur_time_tuple) + (0, 0, 0))
        sunset_time = time.mktime(self.sun_wait.get_sunset_time(cur_time_tuple) + (0, 0, 0))

        if cur_time - sunrise_time < 0:  # Avant le lever du soleil
            raw_sleep_time = sunrise_time - cur_time
            sleeptime = raw_sleep_time - self.offset_sec
            __text = f"il est tôt et {raw_sleep_time}s avant le lever du soleil de tout à l'heure\n"
            mode = self.modes[1]
            # Lever de demain
        elif (cur_time - sunset_time) < 0:  # Avant le coucher du soleil
            raw_sleep_time = sunset_time - cur_time
            sleeptime = raw_sleep_time + self.offset_sec
            __text = f"Le soleil va se coucher dans {raw_sleep_time}s\n"
            mode = self.modes[0]
        else:  # Après le coucher du soleil
            tomorrow = date.fromtimestamp(cur_time) + datetime.timedelta(days=1)
            sunrise_time = time.mktime(self.sun_wait.get_sunrise_time(tomorrow.tuple() + (0, 0)) + (0, 0, 0))
            raw_sleep_time = sunrise_time - cur_time
            sleeptime = raw_sleep_time - self.offset_sec
            __text = f"il est tard et {raw_sleep_time}s avant le lever du soleil de demain matin\n"
            mode = self.modes[1]
        print(__text)
        self.log_txt += __text
        if sleeptime < 0:
            self.log_txt += "ValueError : Sleep time is < 0 !\n"
            raise ValueError("Sleep time is < 0 !")
        return sleeptime, mode

    def __get_next_step_and_time_debug(self):
        self.log_txt += "debug next step\n"
        self.debug_flag = ~self.debug_flag
        return 3, self.modes[self.debug_flag]

    def __write_log(self):
        with open(LOGFILE, "w") as file:
            file.write(self.log_txt)

    def __toggle_chicken_nurse(self, mode):
        self.led.on()
        if mode == self.modes[0]:
            self.log_txt += f"door is {read_status()} : now closing...\n"
            close_door()
            self.log_txt += f"door {read_status()}.\n"
        elif mode == self.modes[1]:
            self.log_txt += f"door is {read_status()} : now opening...\n"
            open_door()
            self.log_txt += f"door {read_status()}.\n"
        self.led.off()

    def __time_to_string(self, n):
        return f"{n[2]}/{n[1]}/{n[0]} à {n[3]}:{n[4]}:{n[5]}"

    def __pause(self, seconds):
        n = time.localtime()
        __text = f"Nous sommes le {self.__time_to_string(n)}, dodo pendant {seconds}s... zzzzzzz\n"
        print(__text)
        self.log_txt += __text
        self.__write_log()
        if self.use_deep_sleep:
            time.sleep(1)
            saved_hour = RTC().datetime()
            picosleep.seconds(seconds)
            self.clock.datetime(RTC().datetime())
        else:
            time.sleep(seconds)
        n = time.localtime()
        __text = f"... bonjour, nous sommes le {self.__time_to_string(n)}\n"
        print(__text)
        self.log_txt += __text
        self.__write_log()
