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
        chik = ChickenNurse(debug=True, use_deep_sleep=False, verbose=True)
        chik.run()
