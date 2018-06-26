from .prod import *  # noqa

ADMIN_NAME = 'PKW Razem'
ADMIN_EMAIL = 'razem.pkw@gmail.com'

ADMINS = [
    ('PKW Gmail', 'razem.pkw@gmail.com'),
]
ELECTION_ADMINS = ADMINS
MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'pkw@partiarazem.pl'
SERVER_EMAIL = '%s <%s>' % (DEFAULT_FROM_NAME, DEFAULT_FROM_EMAIL)

HELP_EMAIL_ADDRESS = 'pkw@partiarazem.pl'
