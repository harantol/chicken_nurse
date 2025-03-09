import datetime
from datetime import date
# import picosleep
from sun import Sun

from machine import Pin, RTC, lightsleep, Timer
import time

from commandes_moteur import STATUS_CLOSING, STATUS_OPENING, STATUS_CLOSED, STATUS_OPENED, open_door, close_door, stop, \
    read_status
import wlan_connection

BLINK_CLOSING = 100
BLINK_OPENING = 1000
BLINK_INIT = 30
LATITUDE = 45.343167
LONGITUDE = 5.586088
TIME_ZONE = 2
OFFSET_SEC = 1800  # seconds
OFFSET_SEC__DEBUG = 5  # seconds
SLEEP_TIME__DEBUG = 3  # seconds
MAX_SLEEP_DURATION = 71 * 60 * 1000  # milliseconds

LOGFILE = "chicken.log"

MODE_OUVERTURE = "Ouverture"
MODE_FERMETURE = "Fermetrue"


class ChickenNurse:
    def __init__(self, debug=False, use_deep_sleep=True, verbose=False):
        self.led = Pin("LED", Pin.OUT)
        self.led.off()

        self.use_deep_sleep = use_deep_sleep
        self.debug = debug
        self.verbose = verbose
        self.log_txt = ""
        self.clock = None

        self.__init_clock()

        self.lat, self.lon, self.time_zone = LATITUDE, LONGITUDE, TIME_ZONE
        self.sun_wait = Sun(lat=self.lat, lon=self.lon, tzone=self.time_zone)
        if self.debug:
            self.print_("DEBUG")
            self.offset_sec = OFFSET_SEC__DEBUG  # 1800
        else:
            self.offset_sec = OFFSET_SEC

        self._clean_status()
        self.__write_log_file()

    def __init_clock(self):
        timer = Timer()
        timer.init(period=BLINK_INIT, mode=Timer.PERIODIC, callback=self.__blink)
        self.__print_log(f"WIFI connexion......")
        try:
            wlan_connection.connnect(verbose=False)
            wlan_connection.set_local_time()
            self.__print_log(f"WIFI connexion OK.")
            time.sleep(2)
            self.clock = RTC()
            timer.deinit()
        except RuntimeError:
            timer.deinit()
            self.__print_log("WIFI connexion failed, stay opened !")
            self.__open_door(period=2000)
            self.__write_log_file()
            raise RuntimeError('wifi connexion failed')

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

        self.__print_log(f"0- la porte est {read_status()}")

        # Compute sleep duration time:
        if self.debug:
            _sleep_time, mode = self.__get_next_step_and_time__debug()
        else:
            _sleep_time, mode = self.__get_next_step_and_time(loc_time=_time)

        self.__check_status_and_action(mode)

        self.__print_log(
            f"2- Prochaine {mode} le {self.__time_to_string(time.gmtime(_sleep_time + time.mktime(_time)))}")

        # Sleep......
        self.__print_log(f"3- Sleep {_sleep_time:1.2f}s")
        self.__sleep(_sleep_time)
        self.__print_log(f"****************************\n C'est l'heure ! {mode}")

        # ACTION ouverture ou fermeture :
        self.__toggle_chicken_nurse(mode)

        # Attente résiduelle avant
        self.__print_log(f"4- Sleep {2 * self.offset_sec:1.2f}s")
        self.__sleep(int(2 * self.offset_sec))

        self.__write_log_file()

    def __print_log(self, text):
        text = self.__time_to_string(time.localtime()) + " : " + text
        self.print_(text)
        self.log_txt += text + '\n'

    def _clean_status(self):
        self.__print_log('CLEAN STATUS...')
        stop()

    def quit(self):
        stop()

    def print_(self, msg):
        if not self.verbose:
            pass
        else:
            print(msg)

    def __check_status_and_action(self, mode):
        __status = read_status()
        if mode == MODE_OUVERTURE and __status != STATUS_CLOSED:
            self.__close_door()  # La porte ne devrait pas être ouverte !
        elif mode == MODE_FERMETURE and __status != STATUS_OPENED:
            self.__open_door()  # La porte ne devrait pas être fermée !

    def __get_next_step_and_time(self, loc_time=None):

        if loc_time is None:
            cur_time_tuple = time.localtime()
        else:
            cur_time_tuple = loc_time
        cur_time = time.mktime(cur_time_tuple)
        sunrise_time = time.mktime(self.sun_wait.get_sunrise_time(cur_time_tuple) + (0, 0, 0))
        sunset_time = time.mktime(self.sun_wait.get_sunset_time(cur_time_tuple) + (0, 0, 0))
        if sunset_time - sunrise_time < 0:
            raise ValueError('Error in computing sunrise and sunset !!')

        __status = read_status()

        if cur_time - sunrise_time < 0:  # Avant le lever du soleil
            raw_sleep_time = sunrise_time - cur_time
            sleeptime = raw_sleep_time - self.offset_sec
            __text = f"1- il est tôt et {raw_sleep_time}s avant le lever du soleil de tout à l'heure"
            mode = MODE_OUVERTURE
            # Lever de demain
        elif (cur_time - sunset_time) < 0:  # Avant le coucher du soleil
            raw_sleep_time = sunset_time - cur_time
            sleeptime = raw_sleep_time + self.offset_sec
            __text = f"1- Le soleil va se coucher dans {raw_sleep_time}s"
            mode = MODE_FERMETURE
        else:  # Après le coucher du soleil
            tomorrow = date.fromtimestamp(cur_time) + datetime.timedelta(days=1)
            sunrise_time = time.mktime(self.sun_wait.get_sunrise_time(tomorrow.tuple() + (0, 0)) + (0, 0, 0))
            raw_sleep_time = sunrise_time - cur_time
            sleeptime = raw_sleep_time - self.offset_sec
            __text = f"1- il est tard et {raw_sleep_time}s avant le lever du soleil de demain matin"
            mode = MODE_OUVERTURE
        self.__print_log(__text)
        if sleeptime < 0:
            self.log_txt += "ValueError : Sleep time is < 0 !\n"
            raise ValueError("Sleep time is < 0 !")
        return sleeptime, mode

    def __get_next_step_and_time__debug(self):
        self.__print_log("1- debug next step")
        __status = read_status()
        if __status == STATUS_CLOSED or __status == STATUS_CLOSING:
            return SLEEP_TIME__DEBUG, MODE_OUVERTURE
        elif __status == STATUS_OPENED or __status == STATUS_OPENING:
            return SLEEP_TIME__DEBUG, MODE_FERMETURE

    def __write_log_file(self):
        with open(LOGFILE, "a") as file:
            file.write(self.log_txt)
            self.log_txt = ""

    def __blink(self, time):
        self.led.toggle()

    def __toggle_chicken_nurse(self, mode):
        if mode == MODE_FERMETURE:
            self.__print_log(f"door is {read_status()} : now closing...")
            self.__close_door()
            self.__print_log(f"door {read_status()}.\n")
        elif mode == MODE_OUVERTURE:
            self.__print_log(f"door is {read_status()} : now opening...")
            self.__open_door()
            self.__print_log(f"door {read_status()}.")
        else:
            raise ValueError(f"{mode} is unknown")

    def __close_door(self):
        self.__exec_with_blinking(period=BLINK_CLOSING, callable=close_door)

    def __open_door(self, period: int = BLINK_OPENING):
        self.__exec_with_blinking(period=period, callable=open_door)

    def __time_to_string(self, n):
        return f"{n[2]}/{n[1]}/{n[0]} à {n[3]}:{n[4]}:{n[5]}"

    def __sleep(self, seconds):
        self.__print_log(
            f"la porte est {read_status()} dodo pendant {seconds}s...\n zzzzzzz\n zzzzzzz\n zzzzzzz")
        self.__write_log_file()
        if self.use_deep_sleep:
            time.sleep(1)
            self.led.off()
            delay = 0
            while (delay + MAX_SLEEP_DURATION) < (seconds * 1000):
                lightsleep(MAX_SLEEP_DURATION)
                delay += MAX_SLEEP_DURATION
            lightsleep(seconds * 1000 - delay)
            self.clock.datetime(RTC().datetime())
        else:
            self.led.off()
            time.sleep(seconds)
        self.led.on()
        self.__print_log(f"... bonjour, la porte est {read_status()}")
        self.__write_log_file()

    def __exec_with_blinking(self, period: int, callable):
        timer = Timer()
        timer.init(period=period, mode=Timer.PERIODIC, callback=self.__blink)
        callable()
        timer.deinit()
        self.led.off()


if __name__ == "__main__":
    chik = ChickenNurse(debug=True, use_deep_sleep=False, verbose=True)
    chik.run()
