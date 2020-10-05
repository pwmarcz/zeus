
from django.urls import re_path
from zeus.views import trustee

urlpatterns = [
    re_path(r'l/(?P<trustee_email>[^/]+)/(?P<trustee_secret>[^/]+)$',
        trustee.login, name="election_trustee_login"),
]

election_patterns = [
    re_path(r'^home$', trustee.home, name='election_trustee_home'),
    re_path(r'^keygen$', trustee.keygen, name='election_trustee_keygen'),
    re_path(r'^upload_pk$', trustee.upload_pk, name='election_trustee_upload_pk'),
    re_path(r'^check_sk$', trustee.check_sk, name='election_trustee_check_sk'),
    re_path(r'^verify_key$', trustee.verify_key, name='election_trustee_verify_key'),
    re_path(r'^json$', trustee.json_data, name='trustee_json_data'),
]
