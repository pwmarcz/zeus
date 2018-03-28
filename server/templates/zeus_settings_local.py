
from .prod import *  # noqa
from copy import deepcopy

DATABASES = deepcopy(DATABASES)
# Customize your database here:
# DATABASES['default']['host'] = 'localhost'
DATABASES['default']['NAME'] = 'zeus'
DATABASES['default']['USER'] = 'zeus'
DATABASES['default']['PASSWORD'] = '{{ zeus_db_password }}'
DATABASES['default']['HOST'] = '127.0.0.1'
DATABASES['default']['PORT'] = '5432'

ALLOWED_HOSTS = ['localhost', '{{ zeus_domain }}']
SITE_DOMAIN = "{{ zeus_domain }}"
URL_HOST = get_from_env("URL_HOST", "https://{{ zeus_domain }}")
SECURE_URL_HOST = get_from_env("SECURE_URL_HOST", "https://{{ zeus_domain }}")
