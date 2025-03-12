from chicken_nurse import ChickenNurse
from commandes_moteur import force_open_door
if __name__ == "__main__":
    try:
        chik = ChickenNurse(debug=False, use_deep_sleep=False, verbose=True)
        chik.run()
    except:
        print(f'Exception ! open door !')
        force_open_door()

