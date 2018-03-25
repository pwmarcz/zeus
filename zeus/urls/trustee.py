from django.conf.urls import url
from zeus.views import trustee

urlpatterns = [
    url(r'l/(?P<trustee_email>[^/]+)/(?P<trustee_secret>[^/]+)$',
        trustee.login, name="election_trustee_login"),
]

election_patterns = [
    url(r'^home$', trustee.home, name='election_trustee_home'),
    url(r'^keygen$', trustee.keygen, name='election_trustee_keygen'),
    url(r'^upload_pk$', trustee.upload_pk, name='election_trustee_upload_pk'),
    url(r'^check_sk$', trustee.check_sk, name='election_trustee_check_sk'),
    url(r'^verify_key$', trustee.verify_key, name='election_trustee_verify_key'),
    url(r'^json$', trustee.json_data, name='trustee_json_data'),
]
