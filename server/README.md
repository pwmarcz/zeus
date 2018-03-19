# Zeus server configuration

Here's how you deploy Zeus to a new server. You will need Python 3.6.

First, install `pipenv` (see main `README.md`) and ensure packages are
installed:

    pipenv sync
    pipenv shell

Let's say we want to configure a server as `zeus.example.com`.

## Provisioning (`ansible`)

Make sure you have a server with `nginx` installed and configured. If you want
HTTPS, it should have a certificate configured for your server (in the `http`
block).

(TODO)

## Deployment (`fabric`)

To deploy the default branch (`deploy`):

    fab host:zeus.example.com deploy

To deploy a custom branch (for instance, `foo`):

    fab host:zeus.example.com,foo deploy
