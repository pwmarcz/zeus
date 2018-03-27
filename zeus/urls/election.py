from __future__ import absolute_import
from django.conf.urls import include, url

from zeus.urls.trustee import election_patterns
from zeus.views import poll, election

election_patterns = [
    url(r'^$', election.index, name="election_index"),
    url(r'^edit$', election.add_or_update, name='election_edit'),
    url(r'^json$', election.json_data, name='election_json_data'),
    url(r'^polls/', include('zeus.urls.poll')),
    url(r'^polls/(?P<poll_uuid>[^/]+)$', election.index, name="election_poll_index"),
    url(r'^trustees/', include('zeus.urls.trustee')),
    url(r'^trustees/list$', election.trustees_list, name='election_trustees_list'),
    url(r'^trustees/(?P<trustee_uuid>[^/]+)/sendurl$', election.trustee_send_url,
        name='election_trustee_send_url'),
    url(r'^trustees/(?P<trustee_uuid>[^/]+)/delete$', election.trustee_delete,
        name='election_trustee_delete'),
    url(r'^trustee/', include(election_patterns)),
    url(r'^freeze$', election.freeze, name="election_freeze"),
    url(r'^cancel$', election.cancel, name="election_cancel"),
    # superadmin url
    url(r'^endnow$', election.endnow, name="election_endnow"),
    url(r'^close$', election.close, name="election_close"),
    url(r'^start-mixing$', election.start_mixing, name="election_start_mixing"),
    url(r'^report$', election.report, name="election_report"),
    url(r'^close_mixing$', election.close_mixing, name="election_close_mixing"),
    url(r'^mix/(?P<mix_key>[^/]+)$', election.remote_mix, name="election_remote_mix"),
    url(r'^email-voters$', poll.voters_email, name="election_voters_email"),
    url(r'^results/(?P<shortname>.*)-(?P<language>.*)\.pdf$', election.results_file,
        name="election_pdf_results",
        kwargs={'ext': 'pdf'}),
    url(r'^results/(?P<shortname>.*)-(?P<language>.*)\.csv$', election.results_file,
        name="election_csv_results",
        kwargs={'ext': 'csv'}),
    url(r'^results/(?P<shortname>.*)-(?P<language>.*)\.zip$', election.results_file,
        name="election_zip_results",
        kwargs={'ext': 'zip'}),
    url(r'^report.html$', election.report,
        name="election_report",
        kwargs={'format': 'html'}),
    url(r'^stats$', election.public_stats,
        name="election_public_stats"),
]

urlpatterns = [
    url(r'^new$', election.add_or_update, name='election_create'),
    url(r'^(?P<election_uuid>[^/]+)/', include(election_patterns)),

    url(r'^testcookie$', election.test_cookie, name='test_cookie'),
    url(r'^testcookie_2$', election.test_cookie_2, name='test_cookie_2'),
    url(r'^nocookies$', election.nocookies, name='nocookies'),

]
