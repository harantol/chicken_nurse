from chicken_nurse import ChickenNurse
from commandes_moteur import open_door

DEBUG: bool = False
if __name__ == "__main__":
    if not DEBUG:
        try:
            chik = ChickenNurse(debug=False, use_deep_sleep=False, verbose=True)
            chik.run()
        except:
            print(f'Exception ! open door !')
            open_door()
    else:
        from wlan_connection import debug_wlan_connection

        ssid_pwd = [
            ("Androliv", "PTit3F33"),
            ("TitFeeTel", "Montagne09!")
        ]

        debug_wlan_connection(ssid_pwd=ssid_pwd, verbose=True)
