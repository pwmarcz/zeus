from fabric.api import task, env, cd, sudo
from fabric.contrib.files import exists


VENV = '/srv/zeus/virtualenv'
IN_VENV = '. /srv/zeus/virtualenv/bin/activate &&'


@task
def host(hostname, git_branch='deploy'):
    env.hosts = [hostname]
    env.git_branch = git_branch


@task
def deploy():
    ensure_virtualenv()
    stop()
    update_source()
    update_python()
    start()


@task
def ensure_virtualenv():
    if not exists(VENV):
        sudo(f'virtualenv --python=python2 {VENV}', user='zeus')
        sudo(f'{IN_VENV} pip install pipenv', user='zeus')

@task
def stop():
    sudo('systemctl stop zeus-uwsgi.service')


@task
def start():
    sudo('systemctl start zeus-uwsgi.service')


@task
def update_source():
    with cd('/srv/zeus/install'):
        sudo('git fetch', user='zeus')
        sudo(f'git reset --hard origin/{env.git_branch}', user='zeus')


@task
def update_python():
    with cd('/srv/zeus/install'):
        sudo(f'{IN_VENV} pipenv sync --bare', user='zeus')
