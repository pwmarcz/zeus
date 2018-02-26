# The Zeus election server

[![Build Status](https://travis-ci.org/pwmarcz/zeus.svg?branch=master)](https://travis-ci.org/pwmarcz/zeus)

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

If necessary, create a Postgres user:

    sudo -u postgres createuser -s $(whoami)

Create a database:

    createdb helios

Ensure you have Python 2.7 and virtualenv. Setup virtualenv:

    ./setup-virtualenv

Activate virtualenv:

    . env/bin/activate

Run migrations:

    python manage.py migrate

## Run

    python manage.py runserver 0.0.0.0:8000

## Test

    python manage.py test

## Python packages

We use [pip-tools](https://github.com/jazzband/pip-tools) to manage
dependencies:

- `requirements.in` - contains list of direct dependencies, not necessarily
  pinned
- `requirements.txt` - auto-generated from `requirements.in`, all packages, all
  versions pinned

In order to install a new package:

- activate virtualenv (`. env/bin/activate`)
- edit `requirements.in`
- run `pip-compile` to generate a new `requirements.txt` file
- run `pip-sync` to install the new packages
- test the change and commit all files
