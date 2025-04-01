"""
Source : https://github.com/itechnofrance/micropython/blob/master/meteo/meteo.py
"""
import requests
import time
from machine import Pin, I2C
import urtc

from gpio_pins import GPIO_RTC_SCL, GPIO_RTC_SDA

url_worldtimeapi = "http://worldtimeapi.org/api/timezone/Europe/Paris"


def get_www(www: str = url_worldtimeapi):
    return requests.get(www, timeout=10)


def get_local_time_from_the_web() -> (time.localtime, int):
    response = get_www(url_worldtimeapi)
    print(response.status_code)
    if response.status_code == 200:
        parsed = response.json()
        print(parsed)
        # {'utc_datetime': '2025-03-20T22:39:05.920774+00:00', 'timezone': 'Europe/Paris',
        #                                                                       , 'utc_offset': '+01:00', 'unixtime': 1742510345, 'week_number': 12, 'raw_offset'
        #                                                                       ': 3600, 'dst_from': None, 'datetime': '2025-03-20T23:39:05.920774+01:00', 'clien
        #                                                                       nt_ip': '92.184.112.172', 'abbreviation': 'CET', 'day_of_year': 79, 'day_of_week'
        #                                                                       ': 4, 'dst': False, 'dst_offset': 0, 'dst_until': None}

        # parsed['unixtime']: local unixtime since 1970/01/01 00:00:00)
        # parsed['raw_offset']: timezone hour offset
        # 946684800: unixtime of 2020/01/01 00:00:00 (system start time on MicroPython)
        # generate datetime tuple based on these information
        return time.localtime(parsed['unixtime'] + parsed['raw_offset'] + parsed['dst_offset']), parsed[
            'raw_offset']  # -> (tm_year,tm_mon,tm_mday,tm_hour,tm_min, tm_sec,tm_wday,tm_yday,tm_isdst)
        # rtc.datetime((year, month, day, weekday, hour, minute, second, microsecond))
    else:
        raise OSError(f'Impossible to access {url_worldtimeapi}')


def set_local_time(max_tries: int = 10) -> (time.localtime, int):
    tries = 0
    while tries <= max_tries:
        print(f"{tries}/{max_tries}...")
        try:
            dt, delta_sec = get_local_time_from_the_web()
            return dt, delta_sec
        except OSError:
            tries += 1
            time.sleep(1)
        except ValueError:
            tries += 1
            time.sleep(1)

    raise RuntimeError(f'Impossible to access {url_worldtimeapi}')


def init_rtc_ds3231() -> urtc.DS3231:
    i2c_rtc = I2C(0, scl=Pin(GPIO_RTC_SCL), sda=Pin(GPIO_RTC_SDA))
    return urtc.DS3231(i2c_rtc)
