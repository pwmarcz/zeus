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

    libicu-dev libgmp-dev libmpfr-dev libmpc-dev

If necessary, create a Postgres user. Then create a database:

    sudo -u postgres createuser -s $(whoami)
    createdb helios

Ensure you have Python 2.7 and [pipenv](https://docs.pipenv.org/)
installed. You can install `pipenv` by running `pip install --user
pipenv`, but make sure it ends up in your `PATH` (e.g. add `export
PATH=$PATH:$HOME/.local/bin` to your `.bashrc`).

Then, do the following:

    pipenv --python python2
    pipenv sync --dev
    pipenv shell

This will create a virtualenv for you, install all the required packages
(including the ones needed for development) and activate the virtual
environment.

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

    celery worker -l INFO

## Test

    pytest -v

## Python packages

We use [pipenv](https://docs.pipenv.org/) to manage dependencies:

- `Pipfile` - contains a list of direct dependencies, with version specifiers
- `Pipfile.lock` - auto-generated from `Pipfile`, all packages, all
  versions pinned together with their checksums

In order to install a new package:

- `pipenv install <package>`
- look into `Pipfile` to make sure the right package was added
- test the change and commit all files
