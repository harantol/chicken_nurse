import network
import time


def disconnect(wlan: network.WLAN):
    wlan.disconnect()
    wlan.active(False)
    wlan.deinit()
    wlan = None
    time.sleep_ms(100)


def connnect(verbose=True) -> network.WLAN:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Sosh", "PTit3F33")
    wait = 100
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
    return wlan
