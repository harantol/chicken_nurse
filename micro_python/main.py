from chicken_nurse import ChickenNurse, datetime_to_string
from commandes_moteur import open_door

DEBUG: bool = False
from machine import RTC
if __name__ == "__main__":
    if not DEBUG:
        while True:
            try:
                chik = ChickenNurse(debug=False, use_deep_sleep=False, verbose=True, full_verbose=False)
                chik.run()
            except:
                with open(f"exception.txt", "w") as file:
                    txt = f'{datetime_to_string(RTC().datetime())} || Exception ! open door !'
                    file.write(txt)
                print(txt)
                open_door()
    else:
        chik = ChickenNurse(debug=True, use_deep_sleep=False, verbose=True, full_verbose=True)
        chik.run()



