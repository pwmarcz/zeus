# Zeus server configuration

Here's how you deploy Zeus to a new server.

## Install software (`ansible`)

You will need Python 3.6.

First, install `pipenv` (see main `README.md`) and ensure packages are
installed:

    pipenv sync
    pipenv shell

## Prepare server

The current Ansible playbook has been tested with Ubuntu 16.04.

Make sure you have a server with `nginx` installed and configured. You should
be able to connect to it (using `ssh example.com`) and have sudo rights.

If you want HTTPS, it should have a certificate configured for your server (in
the `http` block).

## Prepare configuration files

Copy `hosts_example.yml` to `hosts.yml`, customize.

Create a secrets file with all passwords generated:

    ./generate-secrets secrets/zeus-secrets-example.com.json

## Apply the configuration on server

Apply with:

    ansible-playbook zeus.yml -i hosts.yml
