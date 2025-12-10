import network
import time


def disconnect(wlan: network.WLAN):
    wlan.disconnect()
    wlan.active(False)
    wlan.deinit()
    wlan = None
    time.sleep_ms(100)


def connnect(verbose=True) -> network.WLAN:
    ssid_pwd: [str, str] = [
        ("TitFeeTel", "Montagne09!"),
        ("Sosh", "Tit3F33")
    ]
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    for (ssid, pwd) in ssid_pwd:
        if verbose:
            print(f"Connecting to {ssid}...")
        wlan.connect(ssid, pwd)
        wait_max = 10
        wait = wait_max
        while wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                if wlan.status() == 3:
                    if verbose:
                        print(f'connected to {ssid}')
                        print('IP: ', wlan.ifconfig()[0])
                    return wlan
            wait -= 1
            if verbose:
                print(f'waiting for connection {wait}/{wait_max}')
            time.sleep(1)
    if wlan.status() != 3:
        raise RuntimeError('wifi NOK')
    else:
        if verbose:
            print('connected')
            print('IP: ', wlan.ifconfig()[0])
    return wlan


def debug_wlan_connection(ssid_pwd=[
    ("TitFeeTel", "Montagne09!"),
    ("Sosh", "PTit3F33")
], verbose: bool = False):
    import network
    import requests
    wlan = connnect(ssid_pwd=ssid_pwd, verbose=verbose)
    time.sleep(5)
    www = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    print('IP: ', wlan.ifconfig()[0])
    r = requests.get(www)
    print(r.content)

