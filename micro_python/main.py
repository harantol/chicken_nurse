import picosleep
import time
from utime import localtime
from machine import Pin
from sun import Sun
import datetime
from datetime import date
LAT = 45.343167
LON = 5.586088
TZ = 2

modes = ['Fermeture', 'Ouverture']

def get_sleep_time(loc_time = None):
    sun_wait = Sun(lat=LAT, lon=LON, tzone=TZ)
    if loc_time is None:
        cur_time_tuple = localtime()
    else:
        cur_time_tuple = loc_time
    cur_time = time.mktime(cur_time_tuple)
    sunrise_time = time.mktime(sun_wait.get_sunrise_time(cur_time_tuple)+ (0,0,0))
    sunset_time = time.mktime(sun_wait.get_sunset_time(cur_time_tuple)+ (0,0,0))

    if cur_time - sunrise_time < 0: # Avant le lever du soleil
        print("Avant le lever du soleil")
        sleeptime = sunrise_time - cur_time
        mode = modes[1]
        # Lever de demain
    elif (cur_time - sunset_time)<0: # Avant le coucher du soleil
        print("Avant le coucher du soleil")
        sleeptime = sunset_time - cur_time
        mode = modes[0]
    else:# Après le coucher du soleil
        print("Après le coucher du soleil")
        tomorrow = date.fromtimestamp(cur_time) + datetime.timedelta(days=1)
        sunrise_time = time.mktime(sun_wait.get_sunrise_time(tomorrow.tuple()+ (0,0))+(0,0,0))
        sleeptime = sunrise_time - cur_time
        mode = modes[1]
    if sleeptime < 0:
        raise ValueError("Sleep time is < 0 !")
    return sleeptime, mode
    
        
if __name__ == "__main__":
    loc = localtime()
    #loc = (2023, 12, 31, 21, 34, 0, 5, 273)
    print(f"il est {loc}")
    sleeptime, mode = get_sleep_time(loc_time = loc)
    print(f"Prochaine {mode} à {time.gmtime(sleeptime + time.mktime(loc))} dodo pendant {sleeptime}s")
    #picosleep.seconds(2)
    time.sleep(sleeptime)
    print(f"C'est l'heure ! {mode} à {localtime()}")
