import json
from base64 import b64decode

import pytest

from django.test.client import Client
from django.core.urlresolvers import reverse

from zeus.views import shared


@pytest.mark.django_db
def test_get_randomness():
    client = Client()
    response = client.get(reverse('get_randomness'), {})
    assert response['Content-Type'] == 'application/json'
    data = json.loads(response.content)
    assert len(b64decode(data['randomness'])) == 32
    assert 'token' not in data

    response = client.get(reverse('get_randomness'), {'token': 1})
    data = json.loads(response.content)
    assert len(data.get('token', '')) > 0
