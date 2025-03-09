from chicken_nurse import ChickenNurse
from wlan_connection import connnect
import network
import urequests as requests
import time
if __name__ == "__main__":
    #chik = ChickenNurse(debug=True, use_deep_sleep=False, verbose=True)
    #chik.run()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Androliv", "PTit3F33")
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
    time.sleep(5)
    www="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    print('IP: ', wlan.ifconfig()[0])
    r = requests.get(www)
    print(r.content)

