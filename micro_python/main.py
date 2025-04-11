from chicken_nurse import ChickenNurse
from commandes_moteur import open_door
import os
DEBUG: bool = False
from machine import RTC
if __name__ == "__main__":
    if not DEBUG:
        while True:
            try:
                chik = ChickenNurse(debug=False, use_deep_sleep=False, verbose=True, full_verbose=False)
                chik.run()
            except:
                t = RTC().datetime()
                with open(f"exception.txt", "a") as file:
                    file.write(f'{t} Exception ! open door !')
                print(f'Exception ! open door !')
                open_door()
    else:
        chik = ChickenNurse(debug=True, use_deep_sleep=False, verbose=True, full_verbose=True)
        chik.run()


