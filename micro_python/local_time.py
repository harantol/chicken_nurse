"""
Source : https://github.com/itechnofrance/micropython/blob/master/meteo/meteo.py
"""
import requests
import urequests
import time
from machine import RTC

url_worldtimeapi = "http://worldtimeapi.org/api/timezone/Europe/Paris"


def get_www(www: str = url_worldtimeapi):
    return requests.get(www, timeout=10)


def get_local_time():
    response = get_www(url_worldtimeapi)
    print(response.status_code)
    if response.status_code == 200:
        parsed = response.json()
        print(parsed)
        # parsed['unixtime']: local unixtime since 1970/01/01 00:00:00)
        # parsed['raw_offset']: timezone hour offset
        # 946684800: unixtime of 2020/01/01 00:00:00 (system start time on MicroPython)
        # generate datetime tuple based on these information
        return time.localtime(parsed['unixtime'] + parsed['raw_offset'] - 946684800)
        # rtc.datetime((year, month, day, weekday, hour, minute, second, microsecond))
    else:
        raise OSError(f'Impossible to access {url_worldtimeapi}')


def set_local_time(rtc: RTC = RTC()) -> None:
    tries = 0
    while tries < 11:
        print(f"{tries}/10...")
        try:
            dt = get_local_time()
            rtc.datetime((dt[0], dt[1], dt[2], dt[6], dt[3], dt[4], dt[5], 0))
            return
        except OSError:
            tries += 1
    raise OSError(f'Impossible to access {url_worldtimeapi}')
