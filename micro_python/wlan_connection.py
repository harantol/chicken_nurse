import network
import time
import ntptime


def connnect(verbose=True):
    ntptime.host = "1.europe.pool.ntp.org"
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Androliv", "PTit3F33")
    wait = 10
    while wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        wait -= 1
        if verbose:
            print('waiting for connection')
        time.sleep(1)
    if wlan.status() != 3:
        raise RuntimeError('wifi connexion failed')
    else:
        if verbose:
            print('connected')
            print('IP: ', wlan.ifconfig()[0])


def set_local_time():
    ntptime.host = "1.europe.pool.ntp.org"
    ntptime.settime()
