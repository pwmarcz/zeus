from .prod import *  # noqa

ADMIN_NAME = 'Paweł Marczewski'
ADMIN_EMAIL = 'pwmarcz+zeus@gmail.com'

ADMINS = [
    (ADMIN_NAME, ADMIN_EMAIL),
]
ELECTION_ADMINS = ADMINS
MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'zeus@zeus.pwmarcz.pl'
SERVER_EMAIL = '%s <%s>' % (DEFAULT_FROM_NAME, DEFAULT_FROM_EMAIL)

HELP_EMAIL_ADDRESS = 'pwmarcz+zeushelp@gmail.com'
