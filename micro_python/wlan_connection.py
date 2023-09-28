import network
import time

def connnect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Livebox-431A", "PTit3F33")
    wait = 10
    while wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        wait -= 1
        print('waiting for connection')
        time.sleep(1)
    if wlan.status() != 3:
        raise RuntimeError('wifi connexion failed')
    else:
        print('connected')
        print('IP: ', wlan.ifconfig()[0])

