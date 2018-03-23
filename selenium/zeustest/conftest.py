import pytest
import os
import json

from .pages import MainPage


@pytest.fixture
def config():
    path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if not os.path.isfile(path):
        raise Exception('You need to provide config.json.')
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def main_page(selenium, config):
    selenium.get(config['site_url'])
    main_page = MainPage(selenium, config['site_url'])
    main_page.verify()
    return main_page
