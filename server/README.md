# Zeus server configuration

Here's how you deploy Zeus to a new server. You will need Python 3.6.

First, install `pipenv` (see main `README.md`) and ensure packages are
installed:

    pipenv sync
    pipenv shell

Let's say we want to configure a server as `example.com`, with Zeus available
at `zeus.example.com`.

## Provisioning (`ansible`)

Make sure you have a server with `nginx` installed and configured. You should
be able to connect to it (using `ssh example.com`) and have sudo rights.

If you want HTTPS, it should have a certificate configured for your server (in
the `http` block).

Copy `hosts_example.yml` to `hosts.yml`, customize:

    all:
      hosts:
        example.com:
          remote_user: johndoe
          zeus_domain: zeus.example.com
          zeus_use_ssl: yes

Apply with:

    ansible-playbook zeus.yml -i hosts.yml

Note that this will generate a database password and cache it in `.secrets/`.

## Deployment (`fabric`)

To deploy the default branch (`prod`):

    fab host:example.com deploy

To deploy a custom branch (for instance, `foo`):

    fab host:example.com,foo deploy
