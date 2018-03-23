import pytest
import os
import json
import subprocess
import socket
import time

from .pages import MainPage


@pytest.fixture(scope='session')
def config():
    path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if not os.path.isfile(path):
        raise Exception('You need to provide config.json.')
    with open(path) as f:
        return json.load(f)


@pytest.fixture(autouse=True, scope='session')
def testserver(config):
    if not config.get('run_testserver'):
        yield
        return

    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'settings.selenium'
    addr, port = '127.0.0.1', '8000'
    p = subprocess.Popen(
        [
            'pipenv', 'run', 'python', 'manage.py',
            'testserver', '--noinput', 'fixtures/selenium.json',
            '--addrport', addr+':'+port,
        ],
        cwd=os.path.join(os.path.dirname(__file__), '..', '..'),
        env=env
    )

    wait_for_connection((addr, port))
    try:
        yield
    finally:
        p.kill()
        p.wait()


def wait_for_connection(addr, seconds=10):
    start = time.time()
    while time.time() - start < 10:
        try:
            socket.create_connection(addr).close()
        except socket.error:
            pass
        else:
            return
        time.sleep(0.1)
    raise Exception(f'Timed out waiting for {addr}')


@pytest.fixture
def main_page(selenium, config):
    selenium.get(config['site_url'])
    main_page = MainPage(selenium, config['site_url'])
    main_page.verify()
    return main_page
