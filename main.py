from helpers.constants import NEED_LOGIN, PASSWORD, USERNAME
import multiprocessing
from views.main_view import MainView


if __name__ == '__main__':
    multiprocessing.freeze_support()
    if NEED_LOGIN:
        logged = False
        try:
            import requests
            result = requests.get("http://45.117.80.168:8888/" + USERNAME + "/" + PASSWORD).json()
            if 'limit' in result and result['limit'] >= 0:
                logged = True
        except Exception as e:
            pass
        if not logged:
            exit()
    MainView()
