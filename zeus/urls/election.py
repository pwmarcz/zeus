
from django.urls import include, re_path

from zeus.urls.trustee import election_patterns
from zeus.views import poll, election

election_patterns = [
    re_path(r'^$', election.index, name="election_index"),
    re_path(r'^edit$', election.add_or_update, name='election_edit'),
    re_path(r'^json$', election.json_data, name='election_json_data'),
    re_path(r'^polls/', include('zeus.urls.poll')),
    re_path(r'^polls/(?P<poll_uuid>[^/]+)$', election.index, name="election_poll_index"),
    re_path(r'^trustees/', include('zeus.urls.trustee')),
    re_path(r'^trustees/list$', election.trustees_list, name='election_trustees_list'),
    re_path(r'^trustees/(?P<trustee_uuid>[^/]+)/sendurl$', election.trustee_send_url,
        name='election_trustee_send_url'),
    re_path(r'^trustees/(?P<trustee_uuid>[^/]+)/delete$', election.trustee_delete,
        name='election_trustee_delete'),
    re_path(r'^trustee/', include(election_patterns)),
    re_path(r'^freeze$', election.freeze, name="election_freeze"),
    re_path(r'^cancel$', election.cancel, name="election_cancel"),
    re_path(r'^recompute$', election.recompute_results, name="election_recompute_results"),
    re_path(r'^endnow$', election.endnow, name="election_endnow"),
    re_path(r'^close$', election.close, name="election_close"),
    re_path(r'^start-mixing$', election.start_mixing, name="election_start_mixing"),
    re_path(r'^report$', election.report, name="election_report"),
    re_path(r'^close_mixing$', election.close_mixing, name="election_close_mixing"),
    re_path(r'^mix/(?P<mix_key>[^/]+)$', election.remote_mix, name="election_remote_mix"),
    re_path(r'^email-voters$', poll.voters_email, name="election_voters_email"),
    re_path(r'^results/(?P<shortname>.*)-(?P<language>.*)\.pdf$', election.results_file,
        name="election_pdf_results",
        kwargs={'ext': 'pdf'}),
    re_path(r'^results/(?P<shortname>.*)-(?P<language>.*)\.csv$', election.results_file,
        name="election_csv_results",
        kwargs={'ext': 'csv'}),
    re_path(r'^results/(?P<shortname>.*)-(?P<language>.*)\.zip$', election.results_file,
        name="election_zip_results",
        kwargs={'ext': 'zip'}),
    re_path(r'^report.html$', election.report,
        name="election_report",
        kwargs={'format': 'html'}),
    re_path(r'^stats$', election.public_stats,
        name="election_public_stats"),
]

urlpatterns = [
    re_path(r'^new$', election.add_or_update, name='election_create'),
    re_path(r'^(?P<election_uuid>[^/]+)/', include(election_patterns)),

    re_path(r'^testcookie$', election.test_cookie, name='test_cookie'),
    re_path(r'^testcookie_2$', election.test_cookie_2, name='test_cookie_2'),
    re_path(r'^nocookies$', election.nocookies, name='nocookies'),

]
