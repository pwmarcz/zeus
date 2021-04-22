#!/usr/bin/env python

import os
import sys

# HACK until we upgrade Kombu.
# See https://stackoverflow.com/questions/34198538/cannot-import-name-uuid-generate-random-in-heroku-django
import uuid
uuid._uuid_generate_random = None

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
