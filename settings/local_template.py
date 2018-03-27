from __future__ import absolute_import
from .dev import *  # noqa
from copy import deepcopy

DATABASES = deepcopy(DATABASES)
# Customize your database here:
# DATABASES['default']['host'] = 'localhost'
