
from .{{ zeus_settings }} import *  # noqa
from copy import deepcopy

DATABASES = deepcopy(DATABASES)
# Customize your database here:
# DATABASES['default']['host'] = 'localhost'
DATABASES['default']['NAME'] = SECRETS.get('db_name', 'zeus')
DATABASES['default']['USER'] = SECRETS.get('db_user', 'zeus')
DATABASES['default']['PASSWORD'] = SECRETS.get('db_password', 'zeus')
DATABASES['default']['HOST'] = SECRETS.get('db_host', '127.0.0.1')
DATABASES['default']['PORT'] = SECRETS.get('db_port', '5432')

ALLOWED_HOSTS = ['localhost', '{{ zeus_domain }}']
SITE_DOMAIN = "{{ zeus_domain }}"
URL_HOST = get_from_env("URL_HOST", "https://{{ zeus_domain }}")
SECURE_URL_HOST = get_from_env("SECURE_URL_HOST", "https://{{ zeus_domain }}")
