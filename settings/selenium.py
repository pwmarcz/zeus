from .test import *
from copy import deepcopy

DATABASES = deepcopy(DATABASES)
DATABASES['default']['TEST'] = {
    'NAME': 'test_helios_selenium'
}

ALLOWED_HOSTS = ['localhost']

URL_HOST = 'http://localhost:8000'
SECURE_URL_HOST = 'http://localhost:8000'

DEBUG = True  # serve static files
