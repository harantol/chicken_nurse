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


def get_local_time_from_the_web()->(time.localtime, int):
    response = get_www(url_worldtimeapi)
    print(response.status_code)
    if response.status_code == 200:
        parsed = response.json()
        print(parsed)
        # parsed['unixtime']: local unixtime since 1970/01/01 00:00:00)
        # parsed['raw_offset']: timezone hour offset
        # 946684800: unixtime of 2020/01/01 00:00:00 (system start time on MicroPython)
        # generate datetime tuple based on these information
        return time.localtime(parsed['unixtime'] + parsed['raw_offset']), parsed['raw_offset']
        # rtc.datetime((year, month, day, weekday, hour, minute, second, microsecond))
    else:
        raise OSError(f'Impossible to access {url_worldtimeapi}')


def set_local_time() -> (time.localtime, int):
    tries = 0
    max_tries = 100
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
