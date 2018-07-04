# Zeus server configuration

Here's how you deploy Zeus to a new server.

## Install software (`ansible`)

See [Ansible documentation](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-the-control-machine)
on how to install it. You can probably use your system's package repository
(`apt install ansible`).

Alternatively, install the latest version via `pip`:
`pip3 install --user --upgrade ansible`.

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
