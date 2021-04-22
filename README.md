# The Zeus election server

[![Build Status](https://travis-ci.org/pwmarcz/zeus.svg?branch=master)](https://travis-ci.org/pwmarcz/zeus)
[![codecov](https://codecov.io/gh/pwmarcz/zeus/branch/master/graph/badge.svg)](https://codecov.io/gh/pwmarcz/zeus)
[![Requirements Status](https://requires.io/github/pwmarcz/zeus/requirements.svg?branch=master)](https://requires.io/github/pwmarcz/zeus/requirements/?branch=master)

LICENCE: This code is released under the GPL v3 or later

This is a fork of Ben Adida's Helios server. The differences from Helios are as follows:

* Whereas Helios produces election results, Zeus produces a tally of the ballots cast.

* This allows Zeus to be used in voting systems other than approval voting (which is supported
  by Helios), since the vote tally can be fed to any other system that actually produces the
  election results.

* In terms of overall architecture and implementation it is closer to the [original Helios
  implementation](http://static.usenix.org/events/sec08/tech/full_papers/adida/adida.pdf) than Helios v. 3.


## Install

Install Postgres (`postgres-server`, `libpq-dev`).

Install the following libraries:

    libgmp-dev libmpfr-dev libmpc-dev

If necessary, create a Postgres user. Then create a database:

    sudo -u postgres createuser -s $(whoami)
    createdb helios

Ensure you have Python 3.6 or later installed.

Then, do the following:

    python3 -m venv env/
    . env/bin/activate
    pip install -r requirements.txt

This will create a virtualenv for you, activate it, and install all the
required packages.

Create a local Django settings file. This will be an unversioned file that you
can then customize.

    cp settings/local_template.py settings/local.py

Run migrations:

    python manage.py migrate

Create an institution and admin user:

    python manage.py manage_users --create-institution "ZEUS"
    python manage.py manage_users --create-user <username> --institution=1 --superuser

## Run

    python manage.py runserver 0.0.0.0:8000

### Celery

By default, in development all Celery tasks run synchronously. If you
want to run a Celery worker, first disable this behaviour by editing
`settings/local.py`:

    CELERY_TASK_ALWAYS_EAGER = False

You need to also install `redis` and make sure it's running on
localhost.

Then, run:

    celery worker -A zeus.celery -l INFO

## Test

    pytest -v

## Python packages

We use [pip-tools](https://github.com/jazzband/pip-tools) to manage dependencies:

- `requirements.in` - contains a list of direct dependencies, with version
  specifiers if necessary
- `requirements.txt` - auto-generated from `requirements.in`, all packages, all
  versions pinned

In order to install a new package:

- add it to `requirements.in`
- run `pip-compile` to regenerate the list of packages (`requirements.txt`)
- run `pip-sync` to reinstall them
