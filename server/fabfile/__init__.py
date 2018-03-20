from fabric.api import task, env, cd, sudo, hide
from fabric.contrib.files import exists

GIT_REPO = 'https://github.com/pwmarcz/zeus.git'

VENV = '/srv/zeus/virtualenv'
IN_VENV = '. /srv/zeus/virtualenv/bin/activate &&'


@task
def host(hostname, git_branch='prod'):
    env.hosts = [hostname]
    env.git_branch = git_branch


@task
def deploy():
    ensure_virtualenv()
    stop()
    update_source()
    update_python()
    collect_static_files()
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
    if not exists('/srv/zeus/install'):
        sudo(f'git clone {GIT_REPO} /srv/zeus/install', user='zeus')
    with cd('/srv/zeus/install'):
        sudo('git fetch', user='zeus')
        sudo(f'git reset --hard origin/{env.git_branch}', user='zeus')
        sudo('ln -sf /srv/zeus/config/settings_local.py settings/local.py', user='zeus')


@task
def update_python():
    with cd('/srv/zeus/install'), hide('output'):
        sudo(f'{IN_VENV} pipenv sync --bare', user='zeus')


@task
def collect_static_files():
    with cd('/srv/zeus/install'), hide('output'):
        sudo('rm -rf sitestatic')
        sudo(f'{IN_VENV} python manage.py collectstatic --noinput', user='zeus')
