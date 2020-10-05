
from django.urls import include, re_path
from zeus.views import poll, shared

poll_patterns = [
    re_path(r'^get-randomness$', shared.get_randomness),
]

poll_patterns += [
    re_path(r'^remove$', poll.remove, name='election_poll_remove'),
    re_path(r'^edit$', poll.add_edit, name='election_poll_edit'),
    re_path(r'^cast$', poll.cast, name='election_poll_cast'),
    re_path(r'^cast-done$', poll.cast_done, name='election_poll_cast_done'),
    re_path(r'^audited-ballot$', poll.audited_ballots,
        name='election_poll_audited_ballots'),
    re_path(r'^post-audited-ballot$', poll.post_audited_ballot,
        name='election_poll_post_audited_ballot'),
    re_path(r'^s/(?P<fingerprint>.*)$', poll.download_signature,
        name='election_poll_download_signature'),
    re_path(r'^questions$', poll.questions, name='election_poll_questions'),
    re_path(r'^questions/manage$', poll.questions_manage,
        name='election_poll_questions_manage'),
    re_path(r'^voters$', poll.voters_list,
        name='election_poll_voters'),
    re_path(r'^encrypted-tally$', poll.get_tally, name='election_poll_get_tally'),
    re_path(r'^post-decryptions$', poll.upload_decryption,
        name='election_poll_upload_decryption'),
    re_path(r'^voters/csv/(?P<fname>[^/]+).csv$', poll.voters_csv,
        name='election_poll_voters_csv'),
    re_path(r'^voters/clear$', poll.voters_clear, name='election_poll_voters_clear'),
    re_path(r'^voters/upload$', poll.voters_upload,
        name='election_poll_voters_upload'),
    re_path(r'^voters/upload-cancel$', poll.voters_upload_cancel,
        name='election_poll_voters_upload_cancel'),
    re_path(r'^voters/email$', poll.voters_email, name="election_poll_voters_email"),
    re_path(r'^voters/email/(?P<voter_uuid>[^/]+)$', poll.voters_email, name="election_poll_voter_email"),
    re_path(r'^voters/(?P<voter_uuid>[^/]+)/delete$', poll.voter_delete,
        name="election_poll_voter_delete"),
    re_path(r'^mix/(?P<mix_key>.*)$', poll.remote_mix, name="election_poll_remote_mix"),
    re_path(r'^voters/(?P<voter_uuid>[^/]+)/exclude$', poll.voter_exclude,
        name="election_poll_voter_exclude"),
    re_path(r'^l/(?P<voter_uuid>[^/]+)/linked-booth-login',
        poll.voter_booth_linked_login, name="election_poll_voter_booth_linked_login"),
    re_path(r'^results$', poll.results, name='election_poll_results'),
    re_path(r'^l/(?P<voter_uuid>[^/]+)/(?P<voter_secret>[^/]+)$',
        poll.voter_booth_login, name="election_poll_voter_booth_login"),
    re_path(r'^results$', poll.results, name='election_poll_results'),
    re_path(r'^results.json$', poll.results_json, name='election_poll_results_json'),
    re_path(r'^results-(?P<language>.*).pdf$', poll.results_file, name='election_poll_results_pdf',
        kwargs={'ext': 'pdf'}),
    re_path(r'^results-(?P<language>.*).csv$', poll.results_file, name='election_poll_results_csv',
        kwargs={'ext': 'csv'}),
    re_path(r'^proofs.zip$', poll.zeus_proofs, name='election_poll_zeus_proofs'),
    re_path(r'^sms_delivery$', poll.sms_delivery, name='election_poll_sms_delivery'),
]

urlpatterns = [
    re_path(r'^$', poll.polls_list, name='election_polls_list'),
    re_path(r'^add$', poll.add_edit, name='election_polls_add'),
    re_path(r'^(?P<poll_uuid>[^/]+)/', include(poll_patterns)),
    re_path(r'^(?P<poll_uuid>[^/]+).json', poll.to_json,
        name='election_poll_json'),
]
