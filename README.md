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


## Installation

Here is how to set up Zeus and database on your local machine.

1. Set up environment variables: copy `.env.template` to `.env`, customize.

2. If necessary: install PostgreSQL (e.g. `sudo apt install postgresql`),
   create user and database:

        sudo -u postgres createuser zeus --pwprompt
        createdb zeus --owner zeus

3. Make sure PostgreSQL accepts connections from Docker:

   * In `/etc/postgresql/.../main/postgresql.conf`, add Docker interface
     address (172.17.0.1) to `listen_addresses`, e.g.:

     ```
     listen_addresses = 'localhost,172.17.0.1'
     ```

   * In `/etc/postgresql/.../main/pg_hba.conf`, add a line for Zeus to be able
     to connect from all Docker's networks:

     ```
     # TYPE  DATABASE   USER  ADDRESS      METHOD
     ...
     host    zeus       zeus  172.0.0.0/8  md5
     ```

   * Restart Postgres:

     ```
     sudo systemctl restart postgresql.service
     ```

   * Verify if you can connect from Docker:

     ```
     docker run --rm -it postgres:latest psql -h 172.17.0.1 -U zeus zeus
     ```

5. Set up the initial database: run migrations, create user and institution:

        docker-compose run --rm dev bash

        # inside the container:
        python manage.py manage_users --create-institution "ZEUS"
        python manage.py manage_users --create-user <username> --institution=1 --superuser

## Run (development)

To run Zeus locally:

    docker-compose up

This will run a Django development server under `localhost:8000`. It should
reload automatically as you edit the code. The files will be mounted from host,
so that all changes will be visible inside the container.

To open a shell in the Docker container, for running additional commands:

    docker-compose run --rm dev sh

## Run tests

    docker-compose run --rm dev pytest -v

## Manage Python packages

We use [pip-tools](https://github.com/jazzband/pip-tools) to manage dependencies:

- `requirements.in` - contains a list of direct dependencies, with version
  specifiers if necessary
- `requirements.txt` - auto-generated from `requirements.in`, all packages, all
  versions pinned

In order to install a new package:

- add it to `requirements.in`
- regenerate the list of packages (`requirements.txt`):

        docker-compose run --rm dev pip-compile

- rebuild the container to install new packages:

        docker-compose build

## Run (production)

1. Build the containers:

        docker-compose -f docker-compose-prod.yml build

2. Make sure to edit `.env` and set the right parameters.

3. Run:

        docker-compose -f docker-compose-prod.yml up

This will serve Zeus under `localhost:8000`. You can proxy it from outside, add
SSL, etc.

If you update the code, execute database migrations before restarting:

    docker-compose -f docker-compose-prod.yml run --rm prod python manage.py migrate
