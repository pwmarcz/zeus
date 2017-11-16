import os
import sys

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# this initializes django checks
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from zeus.models import *
from heliosauth.models import *
from heliosauth.auth_systems.password import make_password
from zeus.models import Institution

def main(institution_name, username, password):
    inst, created = Institution.objects.get_or_create(name=institution_name)

    try:
        user = User.objects.get(user_id=username)
    except User.DoesNotExist:
        user = User(user_id=username)

    user.user_type = "password"
    user.name = username
    user.superadmin_p = True
    user.management_p = True
    user.institution = inst
    user.ecounting_account = False
    user.info = {
        "name": username,
        "password": make_password(password)
    }
    user.save()

main(*sys.argv[1:])
