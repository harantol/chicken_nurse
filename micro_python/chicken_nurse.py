import datetime
from datetime import date
# import picosleep
from sun import Sun

from machine import Pin, RTC, lightsleep, Timer
import time

from commandes_moteur import STATUS_CLOSING, STATUS_OPENING, STATUS_CLOSED, STATUS_OPENED, open_door, close_door, stop, \
    read_status

LATITUDE = 45.343167
LONGITUDE = 5.586088
TIME_ZONE = 2
OFFSET_SEC = 1800  # seconds
OFFSET_SEC__DEBUG = 5  # seconds
SLEEP_TIME__DEBUG = 3  # seconds

LOGFILE = "chicken.log"

MODE_OUVERTURE = "Ouverture"
MODE_FERMETURE = "Fermetrue"


class ChickenNurse:
    def __init__(self, debug=False, use_deep_sleep=False, verbose=False):
        self.use_deep_sleep = use_deep_sleep
        self.debug = debug
        self.verbose = verbose
        self.lat, self.lon, self.time_zone = LATITUDE, LONGITUDE, TIME_ZONE
        self.sun_wait = Sun(lat=self.lat, lon=self.lon, tzone=self.time_zone)
        self.__debug_bool_toggle = True
        if self.debug:
            self.print_("DEBUG")
            self.offset_sec = OFFSET_SEC__DEBUG  # 1800
        else:
            self.offset_sec = OFFSET_SEC
        self.__init_pin()
        self.log_txt = ""
        self.clock = RTC()
        self._clean_status()

    def run(self):
        if self.debug:
            for _ in range(100):
                self.__run_loop()
        else:
            while True:
                self.__run_loop()

    def __run_loop(self):
        # Current time :
        _time = time.localtime()

        # Log Text :
        if not self.debug:
            self.log_txt = ""

        self.__print_log(f"0- Nous sommes le {self.__time_to_string(_time)}, la porte est {read_status()}\n")

        # Compute sleep duration time:
        if self.debug:
            _sleep_time, mode = self.__get_next_step_and_time__debug()
        else:
            _sleep_time, mode = self.__get_next_step_and_time(loc_time=_time)

        self.__print_log(
            f"2- Prochaine {mode} le {self.__time_to_string(time.gmtime(_sleep_time + time.mktime(_time)))}\n")

        # Sleep......
        self.__print_log(f"3- Sleep {_sleep_time:1.2f}s")
        self.__sleep(_sleep_time)

        self.__print_log(
            f"****************************\n C'est l'heure ! {mode} le {self.__time_to_string(time.localtime())}\n")

        # ACTION ouverture ou fermeture :
        self.__toggle_chicken_nurse(mode)

        # Attente résiduelle avant
        self.__print_log(f"4- Sleep {2 * self.offset_sec:1.2f}s")
        self.__sleep(int(2 * self.offset_sec))

        self.__write_log_file()

    def __print_log(self, text):
        self.print_(text)
        self.log_txt += text

    def __init_pin(self):
        self.led = Pin("LED", Pin.OUT)
        self.led.off()

    def _clean_status(self):
        self.__print_log('CLEANING')
        if read_status() == STATUS_CLOSING:
            self.__close_door()
        elif read_status() == STATUS_OPENING:
            self.__open_door()
        else:
            stop()
        stop()

    def quit(self):
        stop()

    def print_(self, msg):
        if not self.verbose:
            pass
        else:
            print(msg)

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
            __text = f"1- il est tôt et {raw_sleep_time}s avant le lever du soleil de tout à l'heure\n"
            mode = MODE_OUVERTURE
            # Lever de demain
        elif (cur_time - sunset_time) < 0:  # Avant le coucher du soleil
            raw_sleep_time = sunset_time - cur_time
            sleeptime = raw_sleep_time + self.offset_sec
            __text = f"1- Le soleil va se coucher dans {raw_sleep_time}s\n"
            mode = MODE_FERMETURE
        else:  # Après le coucher du soleil
            tomorrow = date.fromtimestamp(cur_time) + datetime.timedelta(days=1)
            sunrise_time = time.mktime(self.sun_wait.get_sunrise_time(tomorrow.tuple() + (0, 0)) + (0, 0, 0))
            raw_sleep_time = sunrise_time - cur_time
            sleeptime = raw_sleep_time - self.offset_sec
            __text = f"1- il est tard et {raw_sleep_time}s avant le lever du soleil de demain matin\n"
            mode = MODE_OUVERTURE
        self.print_(__text)
        self.log_txt += __text
        if sleeptime < 0:
            self.log_txt += "ValueError : Sleep time is < 0 !\n"
            raise ValueError("Sleep time is < 0 !")
        return sleeptime, mode

    def __get_next_step_and_time__debug(self):
        self.__print_log("1- debug next step\n")
        self.__debug_bool_toggle = ~self.__debug_bool_toggle
        __status = read_status()
        if __status == STATUS_CLOSED or __status == STATUS_CLOSING:
            return SLEEP_TIME__DEBUG, MODE_OUVERTURE
        elif __status == STATUS_OPENED or __status == STATUS_OPENING:
            return SLEEP_TIME__DEBUG, MODE_FERMETURE

    def __write_log_file(self):
        with open(LOGFILE, "w") as file:
            file.write(self.log_txt)

    def __blink(self, time):
        self.led.toggle()

    def __toggle_chicken_nurse(self, mode):
        if mode == MODE_FERMETURE:
            self.__print_log(f"door is {read_status()} : now closing...\n")
            self.__close_door()
            self.__print_log(f"door {read_status()}.\n")
        elif mode == MODE_OUVERTURE:
            self.__print_log(f"door is {read_status()} : now opening...\n")
            self.__open_door()
            self.__print_log(f"door {read_status()}.\n")
        else:
            raise ValueError(f"{mode} is unknown")

    def __close_door(self):
        timer = Timer()
        timer.init(freq=5, mode=Timer.PERIODIC, callback=self.__blink)
        close_door()
        timer.deinit()
        self.led.on()

    def __open_door(self):
        timer = Timer()
        timer.init(freq=5, mode=Timer.PERIODIC, callback=self.__blink)
        open_door()
        timer.deinit()
        self.led.on()

    def __time_to_string(self, n):
        return f"{n[2]}/{n[1]}/{n[0]} à {n[3]}:{n[4]}:{n[5]}"

    def __sleep(self, seconds):
        n = time.localtime()
        self.__print_log(f"Nous sommes le {self.__time_to_string(n)}, dodo pendant {seconds}s... zzzzzzz\n")
        self.__write_log_file()
        if self.use_deep_sleep:
            time.sleep(1)
            saved_hour = RTC().datetime()
            self.led.off()
            lightsleep(seconds * 1000)
            self.clock.datetime(RTC().datetime())
        else:
            self.led.off()
            time.sleep(seconds)
        self.led.on()
        n = time.localtime()
        self.__print_log(f"... bonjour, nous sommes le {self.__time_to_string(n)}\n")
        self.__write_log_file()
