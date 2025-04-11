import os
from gpio_pins import GPIO_RTC_SCL, GPIO_RTC_SDA, GPIO_RTC_SQW
# import picosleep
from sun import Sun

from machine import Pin, Timer, I2C, RTC, deepsleep
import urtc
import time

from commandes_moteur import STATUS_CLOSING, STATUS_OPENING, STATUS_CLOSED, STATUS_OPENED, open_door, close_door, stop, \
    read_status
import wlan_connection
from oled import OLED
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
DEBUG_SLEEP_TIME = 5  # seconds
MAX_DEEPSLEEP_DURATION_MS = 71 * 60 * 1000  # milliseconds
LOGFILE_BASE = "chicken.log"
MODE_OUVERTURE = "Ouverture"
MODE_FERMETURE = "Fermetrue"

class ChickenNurse:
    def __init__(self,
                 debug: bool = False,
                 use_deep_sleep: bool = True,
                 verbose: bool = False) -> None:

        self.use_deep_sleep = use_deep_sleep
        self.log_file = None
        self.debug = debug
        self.next_mode = None
        self.verbose = verbose
        self.log_txt = ""
        self.log_is_init: bool = False

        self._oled = None

        self.__init_oled()

        self.led = Pin("LED", Pin.OUT)
        self.led.on()

        # DS3231 rtc init
        self.alarm_time: urtc.seconds2tuple = None
        self.rtc = None
        self.__init__rtc()

        self.__init_log_file()

        self.time_zone = TIME_ZONE

        self._stop_door()

        # init clock from the web or the external RTC or the internal RTC
        timer = Timer()
        timer.init(period=BLINK_INIT, mode=Timer.PERIODIC, callback=self.__blink)
        try:
            if self.rtc.lost_power():
                print("RTC lost power !")
                self.__init_clock(max_tries=100)
            else:
                self.__init_clock()
        except RuntimeError as e:
            self.__print_log(str(e))
            self.__print_log(f"FAIL Set local time.")
            if self.rtc.datetime().year == 2000:
                raise RuntimeError("FAIL Set local time and time has never been set !")
            pass
        timer.deinit()

        self.sun_wait = Sun(lat=LATITUDE, lon=LONGITUDE, tzone=self.time_zone)

        if self.debug:
            self.__print_log("%%%%%%%%%%%%%%%% DEBUG %%%%%%%%%%%%%%%%%%%%%")
            self.additional_sleep_time = SUN_OFFSET_SEC__DEBUG
        else:
            self.additional_sleep_time = SUN_OFFSET_SEC

    def __init_oled(self):
        try:
            self._oled = OLED()
            self.log_txt += 'SCREEN OK\n'
            self.print_('SCREEN OK')
        except OSError:
            self.log_txt += 'NO SCREEN\n'
            self.print_('NO SCREEN')
            self._oled = None

    def __init_log_file(self):
        n = self.rtc.datetime()
        self.log_file = f"{n[2]}_{n[1]}_{n[0]}__{n[4]}_{n[5]}_{n[6]}_" + LOGFILE_BASE
        self.__write_log_file('w')  # erase exisiting log
        self.log_is_init = True

    def __init__rtc(self) -> None:
        try:
            i2c_rtc = I2C(0, scl=Pin(GPIO_RTC_SCL), sda=Pin(GPIO_RTC_SDA))

            self.rtc = urtc.DS3231(i2c_rtc)
            self.rtc.datetime()
            # Attach the interrupt callback
            if self.use_deep_sleep:
                sqw_pin = Pin(GPIO_RTC_SQW, Pin.IN, Pin.PULL_UP)
                sqw_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.__run_loop)
            self.__print_log('RTC OK')
        except OSError as e:
            self.__print_log(f'RTC ERROR')
            raise OSError(f'RTC ERROR: {e}')

    def __init_clock(self, max_tries: int = 10):
        if self.rtc is None:
            self.__init__rtc()
        self.__print_log(f"WIFI connexion")
        wlan = wlan_connection.connnect(verbose=True)
        self.__print_log(f"WIFI OK.")
        self.__print_log(f"Set local time")
        time_tuple, delta_sec = set_local_time(max_tries=max_tries)
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
        self.__print_log(f"RUN LOOP")
        self.__print_log(f"door {read_status()}")

        # Compute sleep duration time:
        _sleep_time = self.__compute_sunwait_and_sleep_time(loc_time_tuple=_time)
        if self.debug:
            _sleep_time = self.__get_next_step_and_time__debug(loc_time_tuple=_time)

        self.__check_status_and_action()

        __cur_sec = urtc.tuple2seconds(_time)
        __str_var = self.__datetime_to_string(urtc.seconds2tuple(_sleep_time + __cur_sec))
        self.__print_log(f"next {self.next_mode}: {__str_var}")

        # Sleep......
        self.__print_log(f"Sleep {_sleep_time:1.2f}s....")
        self.__sleep(_sleep_time)

        # Code a priori inaccessible en mode deep sleep:
        if self.use_deep_sleep:
            self.__print_log(f"!!!!!!!!!!!!!!! MODE DEEP SLEEP CODE INACCESSIBLE")
        self.led.on()
        self.__print_log(
            f"C'est l'heure ! door {read_status()} {self.next_mode}")

        # ACTION ouverture ou fermeture :
        self.__toggle_chicken_nurse(self.next_mode)

        # Attente résiduelle avant
        # self.__print_log(f"4- Additional sleep {2 * self.additional_sleep_time:1.2f}s")
        # self.__sleep(int(2 * self.additional_sleep_time))
        self.__print_log(f"********* END RUN LOOP *************]")

    def __print_log(self, text):
        if self._oled is not None:
            self._oled.print(text)
        text = (self.__datetime_to_string(self.rtc.datetime()) + " || " + text)
        self.print_(text)
        self.log_txt += text + '\n'
        self.__write_log_file()

    def _stop_door(self):
        self.__print_log(f'STOP. Door looks {read_status()}.')
        stop()

    def quit(self):
        stop()

    def print_(self, msg):
        if not self.verbose:
            pass
        else:
            print(msg)

    def __check_status_and_action(self):
        __status = read_status()
        if self.next_mode == MODE_OUVERTURE and __status != STATUS_CLOSED:
            if __status == STATUS_OPENING:
                self.__open_door()  # if door was opening, finish it before closing. Else rope may reach over end !!
            self.__close_door()  # La porte ne devrait pas être ouverte !
        elif self.next_mode == MODE_FERMETURE and __status != STATUS_OPENED:
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
            sleep_time_s = raw_sleep_time - self.additional_sleep_time
            __text = (f"il est tôt et {raw_sleep_time}s avant le lever du soleil de tout à l'heure à {today_sunrise_time_tuple}")
            self.next_mode = MODE_OUVERTURE
            # Lever de demain
        elif (cur_time - sunset_time) < 0:  # Avant le coucher du soleil
            raw_sleep_time = sunset_time - cur_time
            sleep_time_s = raw_sleep_time + self.additional_sleep_time
            __text = f"Le soleil va se coucher dans {raw_sleep_time}s à {today_sunset_time_tuple}"
            self.next_mode = MODE_FERMETURE
        else:  # Après le coucher du soleil
            tomorow_list = list(loc_time_tuple)
            tomorow_list[2]+=1
            tomorrow_sunrise_time_tuple = self.sun_wait.get_sunrise_time(tuple(tomorow_list) + (0, 0))
            sunrise_time = time.mktime(tomorrow_sunrise_time_tuple + (0, 0, 0))
            raw_sleep_time = sunrise_time - cur_time
            sleep_time_s = raw_sleep_time - self.additional_sleep_time
            __text = f"il est tard et {raw_sleep_time}s avant le lever du soleil de demain matin à {tomorrow_sunrise_time_tuple}"
            self.next_mode = MODE_OUVERTURE
        self.__print_log(__text)
        if sleep_time_s < 0:
            self.log_txt += "ValueError : Sleep time is < 0 !\n"
            raise ValueError("Sleep time is < 0 !")
        if self.use_deep_sleep:
            self.setup_alarms(sleep_time_s=sleep_time_s, cur_time=cur_time)
        return sleep_time_s

    # Callback for handling alarm interrupt.
    def on_alarm(self):
        self.__print_log("Interrupt")

        if self.rtc.alarm(alarm=0):  # Check if Alarm 1 triggered
            if self.verbose:
                self.__print_log("Alarm 1 trig.")
            self.rtc.alarm(False, alarm=0)  # Clear Alarm 1 flag

    # Setup alarms on the DS3231
    def setup_alarms(self, sleep_time_s: int, cur_time: int):
        _alarm_time = urtc.seconds2tuple(sleep_time_s + cur_time)
        self.alarm_time = urtc.DateTimeTuple(
            year=_alarm_time.year,
            month=_alarm_time.month,
            day=_alarm_time.day,
            hour=_alarm_time.hour,
            minute=_alarm_time.minute,
            second=_alarm_time.second,
            millisecond=_alarm_time.millisecond,
            weekday=None
        )  # rtc.alarm_time can't specify both day and weekday

        # Clear any existing alarms
        self.rtc.alarm(False, 0)
        self.rtc.no_interrupt()

        # Set the desired alarm times
        self.rtc.alarm_time(self.alarm_time, 0)  # Alarm 1

        # Enable interrupts for the alarms
        self.rtc.interrupt(0)
        if self.verbose:
            self.__print_log(f"Alarm set OK")
            self.__print_log(f"{self.__datetime_to_string(self.alarm_time)}.")

    def __get_next_step_and_time__debug(self, loc_time_tuple: urtc.DateTimeTuple)->int:
        self.__print_log("debug : NO SUN, manual next step")
        __status = read_status()
        if self.use_deep_sleep:
            self.setup_alarms(sleep_time_s=DEBUG_SLEEP_TIME, cur_time=urtc.tuple2seconds(loc_time_tuple))

        if __status == STATUS_CLOSED or __status == STATUS_CLOSING:
            self.next_mode = MODE_OUVERTURE
            return DEBUG_SLEEP_TIME
        elif __status == STATUS_OPENED or __status == STATUS_OPENING:
            self.next_mode = MODE_FERMETURE
            return DEBUG_SLEEP_TIME
        else:
            self.__print_log("Impossible de lire le statut : no wait until next step !")
            return 0

    def __write_log_file(self, mode: str = 'a'):
        if not self.log_is_init:
            return
        with open(self.log_file, mode) as file:
            file.write(self.log_txt)
            self.log_txt = ""

    def __blink(self, time):
        self.led.toggle()

    def __toggle_chicken_nurse(self, mode):
        if mode == MODE_FERMETURE:
            if self.verbose:
                self.__print_log(f"door is {read_status()} : now closing...")
            self.__close_door()
            if self.verbose:
                self.__print_log(f"door {read_status()}.")
        elif mode == MODE_OUVERTURE:
            if self.verbose:
                self.__print_log(f"door is {read_status()} : now opening...")
            self.__open_door()
            if self.verbose:
                self.__print_log(f"door {read_status()}.")
        else:
            raise ValueError(f"{mode} is unknown")

    def __close_door(self):
        self.__exec_with_blinking(period=BLINK_CLOSING, callable=close_door)

    def __open_door(self, period: int = BLINK_OPENING):
        self.__exec_with_blinking(period=period, callable=open_door)

    @staticmethod
    def __datetime_to_string(n):
        return f"{n[2]}/{n[1]}/{n[0]} {n[4]:02d}:{n[5]:02d}:{n[6]:02d}"

    def __deep_sleep(self, seconds: int) -> None:
        self.led.off()
        if self.verbose:
            self.__print_log(f"DEEPSLEEP NOW !")
            self.__print_log(f"alarm {self.alarm_time} !")
        deepsleep()

    def __sleep(self, seconds: int) -> None:
        self.__print_log(
            f"door {read_status()}, {seconds}s dodo..\n zzzzzzz\n")
        if self.use_deep_sleep:  # doesn't work...
            self.__deep_sleep(seconds=seconds)
        else:
            self.led.off()
            time.sleep(seconds)

    def __exec_with_blinking(self, period: int, callable):
        timer = Timer()
        timer.init(period=period, mode=Timer.PERIODIC, callback=self.__blink)
        callable()
        timer.deinit()
        self.led.off()


if __name__ == "__main__":
    chik = ChickenNurse(debug=True, use_deep_sleep=False, verbose=True)
    chik.run()
