import os
from urllib.request import urlretrieve


def download_alto():
    file_path = os.path.expanduser(
        "~/tuw_nlp_resources/alto-2.3.6-SNAPSHOT-all.jar")
    user_path = os.path.expanduser("~/tuw_nlp_resources")
    if not os.path.isfile(file_path):
        if not os.path.exists(user_path):
            os.makedirs(user_path)
            from urllib.request import urlretrieve
            urlretrieve(
                'http://sandbox.hlt.bme.hu/~adaamko/alto-2.3.6-SNAPSHOT-all.jar', file_path)
