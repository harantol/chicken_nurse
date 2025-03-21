import datetime
from datetime import date

# import picosleep
from sun import Sun

from machine import Pin, lightsleep, Timer, I2C, RTC
import urtc
import time

from commandes_moteur import STATUS_CLOSING, STATUS_OPENING, STATUS_CLOSED, STATUS_OPENED, open_door, close_door, stop, \
    read_status
import wlan_connection
from local_time import set_local_time

# parameters :
BLINK_CLOSING = 100  # ms
BLINK_OPENING = 1000  # ms
BLINK_INIT = 30  # ms
LATITUDE = 45.343167
LONGITUDE = 5.586088
TIME_ZONE = 1
SUN_OFFSET_SEC = 1800  # seconds
SUN_OFFSET_SEC__DEBUG = 5  # seconds
DEBUG_SLEEP_TIME = 3  # seconds
MAX_DEEPSLEEP_DURATION_MS = 71 * 60 * 1000  # milliseconds
LOGFILE_BASE = "chicken.log"
MODE_OUVERTURE = "Ouverture"
MODE_FERMETURE = "Fermetrue"
GPIO_RTC_SCL = 5
GPIO_RTC_SDA = 4


class ChickenNurse:
    def __init__(self,
                 debug: bool = False,
                 use_deep_sleep: bool = True,
                 verbose: bool = False) -> None:

        self.use_deep_sleep = use_deep_sleep
        self.debug = debug
        self.verbose = verbose
        self.log_txt = ""

        self.led = Pin("LED", Pin.OUT)
        self.led.on()

        # clock
        self.rtc = None
        self.__init__rtc()

        self.time_zone = TIME_ZONE
        self.log_file = LOGFILE_BASE

        # clean door state
        self._clean_status()

        # init clock from the web or the external RTC or the internal RTC
        timer = Timer()
        timer.init(period=BLINK_INIT, mode=Timer.PERIODIC, callback=self.__blink)
        try:
            self.__init_clock()
        except RuntimeError as e:
            self.__print_log(str(e))
            self.__print_log(f"FAIL Set local time.")
            pass
        timer.deinit()

        self.sun_wait = Sun(lat=LATITUDE, lon=LONGITUDE, tzone=self.time_zone)

        if self.debug:
            self.__print_log("%%%%%%%%%%%%%%%% DEBUG %%%%%%%%%%%%%%%%%%%%%")
            self.additional_sleep_time = SUN_OFFSET_SEC__DEBUG
        else:
            self.additional_sleep_time = SUN_OFFSET_SEC

        n = self.rtc.datetime()
        self.log_file = f"{n[2]}_{n[1]}_{n[0]}__{n[4]}_{n[5]}_{n[6]}_" + LOGFILE_BASE
        self.__write_log_file('w')  # erase exisiting log

    def __init__rtc(self) -> None:
        try:
            i2c_rtc = I2C(0, scl=Pin(GPIO_RTC_SCL), sda=Pin(GPIO_RTC_SDA))
            self.rtc = urtc.DS3231(i2c_rtc)
            self.rtc.datetime()
            self.__print_log('RTC OK')
        except OSError as e:
            self.rtc = RTC()
            self.__print_log(f'RTC ERROR')

    def __init_clock(self):
        if self.rtc is None:
            self.__init__rtc()
        self.__print_log(f"WIFI connexion......")
        wlan = wlan_connection.connnect(verbose=True)
        self.__print_log(f"WIFI connexion OK.")
        self.__print_log(f"Set local time ...")
        time_tuple, delta_sec = set_local_time()
        # (tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst)
        self.time_zone = int(delta_sec / 3600)
        initial_time_seconds = time.mktime(time_tuple)  # local time in seconds
        # Convert to tuple compatible with the library
        initial_time = urtc.seconds2tuple(initial_time_seconds)
        self.rtc.datetime(initial_time)
        self.__print_log(f"Set local time OK.")
        time.sleep(2)
        wlan_connection.disconnect(wlan)

    def run(self):
        if self.debug:
            for _ in range(100):
                self.__run_loop()
        else:
            while True:
                self.__run_loop()

    def __run_loop(self):
        # Current time :
        _raw_time = self.rtc.datetime()
        _time = urtc.DateTimeTuple(year=_raw_time[0],
                                   month=_raw_time[1],
                                   day=_raw_time[2],
                                   weekday=_raw_time[3],
                                   hour=_raw_time[4],
                                   minute=_raw_time[5],
                                   second=_raw_time[6],
                                   millisecond=_raw_time[7])
        self.__print_log(f"********* RUN LOOP *************")
        self.__print_log(f"0- la porte est {read_status()}")

        # Compute sleep duration time:
        _sleep_time, mode = self.__compute_sunwait_and_sleep_time(loc_time_tuple=_time)
        if self.debug:
            _sleep_time, mode = self.__get_next_step_and_time__debug()

        self.__check_status_and_action(mode)

        self.__print_log(
            f"2- Prochaine {mode} le {self.__datetime_to_string(urtc.seconds2tuple(_sleep_time + urtc.tuple2seconds(_time)))}")

        # Sleep......
        self.__print_log(f"3- Sleep {_sleep_time:1.2f}s....")
        self.__sleep(_sleep_time)
        self.__print_log(f"****************************\n C'est l'heure ! {mode}")

        # ACTION ouverture ou fermeture :
        self.__toggle_chicken_nurse(mode)

        # Attente résiduelle avant
        # self.__print_log(f"4- Additional sleep {2 * self.additional_sleep_time:1.2f}s")
        # self.__sleep(int(2 * self.additional_sleep_time))
        self.__print_log(f"********* END RUN LOOP *************]")
        self.__write_log_file()

    def __print_log(self, text):
        text = (self.__datetime_to_string(self.rtc.datetime()) + " || " + text)
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

    def __compute_sunwait_and_sleep_time(self, loc_time_tuple: urtc.DateTimeTuple):
        cur_time = urtc.tuple2seconds(loc_time_tuple)  # conversion from urtc to second
        loc_time_tuple = (
            loc_time_tuple.year,
            loc_time_tuple.month,
            loc_time_tuple.day,
            loc_time_tuple.hour,
            loc_time_tuple.minute,
            loc_time_tuple.second,
            loc_time_tuple.weekday,
            0)  # conversion from utc to localtime()
        # From here cur_time is an integer second:
        today_sunrise_time_tuple = self.sun_wait.get_sunrise_time(
            loc_time_tuple)  # input (year, month, mday, hour, minute, second, weekday, yearday)
        today_sunset_time_tuple = self.sun_wait.get_sunset_time(loc_time_tuple)
        sunrise_time = time.mktime(today_sunrise_time_tuple + (0, 0, 0))
        sunset_time = time.mktime(today_sunset_time_tuple + (0, 0, 0))
        if sunset_time - sunrise_time < 0:
            raise ValueError('Error in computing sunrise and sunset !!')

        if cur_time - sunrise_time < 0:  # Avant le lever du soleil
            raw_sleep_time = sunrise_time - cur_time
            sleep_time = raw_sleep_time - self.additional_sleep_time
            __text = (f"1- il est tôt et {raw_sleep_time}s avant le lever du soleil de tout à l'heure"
                      f" à {today_sunrise_time_tuple}")
            mode = MODE_OUVERTURE
            # Lever de demain
        elif (cur_time - sunset_time) < 0:  # Avant le coucher du soleil
            raw_sleep_time = sunset_time - cur_time
            sleep_time = raw_sleep_time + self.additional_sleep_time
            __text = f"1- Le soleil va se coucher dans {raw_sleep_time}s à {today_sunset_time_tuple}"
            mode = MODE_FERMETURE
        else:  # Après le coucher du soleil
            tomorrow = date.fromtimestamp(cur_time) + datetime.timedelta(days=1)
            tomorrow_sunrise_time_tuple = self.sun_wait.get_sunrise_time(tomorrow.tuple() + (0, 0))
            sunrise_time = time.mktime(tomorrow_sunrise_time_tuple + (0, 0, 0))
            raw_sleep_time = sunrise_time - cur_time
            sleep_time = raw_sleep_time - self.additional_sleep_time
            __text = f"1- il est tard et {raw_sleep_time}s avant le lever du soleil de demain matin à {tomorrow_sunrise_time_tuple}"
            mode = MODE_OUVERTURE
        self.__print_log(__text)
        if sleep_time < 0:
            self.log_txt += "ValueError : Sleep time is < 0 !\n"
            raise ValueError("Sleep time is < 0 !")
        return sleep_time, mode

    def __get_next_step_and_time__debug(self):
        self.__print_log("1- debug : NO SUN, manual next step")
        __status = read_status()
        if __status == STATUS_CLOSED or __status == STATUS_CLOSING:
            return DEBUG_SLEEP_TIME, MODE_OUVERTURE
        elif __status == STATUS_OPENED or __status == STATUS_OPENING:
            return DEBUG_SLEEP_TIME, MODE_FERMETURE

    def __write_log_file(self, mode: str = 'a'):
        with open(self.log_file, mode) as file:
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

    @staticmethod
    def __datetime_to_string(n):
        return f"{n[2]}/{n[1]}/{n[0]} à {n[4]:02d}:{n[5]:02d}:{n[6]:02d}"

    def __deep_sleep(self, seconds: int) -> None:
        time.sleep(1)
        self.led.off()
        delay = 0
        while (delay + MAX_DEEPSLEEP_DURATION_MS) < (seconds * 1000):
            lightsleep(MAX_DEEPSLEEP_DURATION_MS)
            delay += MAX_DEEPSLEEP_DURATION_MS
        lightsleep(seconds * 1000 - delay)
        self.__init__rtc()

    def __sleep(self, seconds: int) -> None:
        self.__print_log(
            f"la porte est {read_status()} dodo pendant {seconds}s...\n zzzzzzz\n")
        self.__write_log_file()
        if self.use_deep_sleep:  # doesn't work...
            self.__deep_sleep(seconds=seconds)
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
