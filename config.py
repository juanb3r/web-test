import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or b'\xa5\x8b.\x95}\xc9\xcf\xfc\xe3&\x8f,3\xf1\x9cd'

    MONGODB_SETTINGS = {
        'db': 'UTA_enrollment',
        'host':"mongodb://jeltex:juan123@127.0.0.1:27018/UTA_enrollment"
    }


#python -c "import os; print(os.urandom(16))" imprime clave