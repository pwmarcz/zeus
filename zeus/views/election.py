
import six.moves.urllib.request
import six.moves.urllib.parse
import six.moves.urllib.error
import datetime
import json
import os

from collections import OrderedDict

from zeus.forms import ElectionForm
from zeus.utils import election_reverse
from zeus.views.utils import set_menu

from zeus import tasks
from zeus import reports
from zeus import auth

from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext_lazy as _

from helios.view_utils import render_template
from helios.models import Voter


@transaction.atomic
@auth.election_admin_required
@require_http_methods(["GET", "POST"])
def add_or_update(request, election=None):
    user = request.admin
    institution = user.institution

    if request.method == "GET":
        election_form = ElectionForm(user, institution, instance=election,
                                     lang=request.LANGUAGE_CODE)
    else:
        election_form = ElectionForm(user, institution, request.POST,
                                     instance=election)

    if election_form.is_valid():
        creating = election is None
        with transaction.atomic():
            election = election_form.save()
            if not election.admins.filter(pk=user.pk).count():
                election.admins.add(user)
            if election_form.creating:
                election.logger.info("Election created")
                msg = "New election created"
                subject = "New Zeus election"
                election.notify_admins(msg=msg, subject=subject)
            if not election.has_helios_trustee():
                election.generate_trustee()
            if election.polls.count() == 0:
                url = election_reverse(election, 'polls_add')
            else:
                url = election_reverse(election, 'index')
            if election.voting_extended_until:
                subject = "Voting extension"
                msg = "Voting end date extended"
                election.notify_admins(msg=msg, subject=subject)

            election.zeus.compute_election_public()
            election.logger.info("Public key updated")
            hook_url = None
            if creating:
                hook_url = election.get_module().run_hook('post_create')
            else:
                hook_url = election.get_module().run_hook('post_update')
            return HttpResponseRedirect(hook_url or url)

    context = {'election_form': election_form, 'election': election}
    set_menu('election_edit', context)
    tpl = "election_new"
    if election and election.pk:
        tpl = "election_edit"
    return render_template(request, tpl, context)


@auth.election_user_required
@require_http_methods(["GET"])
def trustees_list(request, election):
    trustees = election.trustees.filter(election=election,
                                        secret_key__isnull=True).order_by('pk')

    # TODO: can we move this in a context processor
    # or middleware ???
    voter = None
    poll = None
    if getattr(request, 'voter', None):
        voter = request.voter
        poll = voter.poll

    context = {
        'election': election,
        'poll': poll,
        'voter': voter,
        'trustees': trustees
    }
    set_menu('trustees', context)
    return render_template(request, 'election_trustees_list', context)


@auth.election_admin_required
@auth.requires_election_features('can_send_trustee_email')
@require_http_methods(["POST"])
def trustee_send_url(request, election, trustee_uuid):
    trustee = election.trustees.get(uuid=trustee_uuid)
    trustee.send_url_via_mail()
    url = election_reverse(election, 'trustees_list')
    messages.success(request, _("Trustee login url sent"))
    return HttpResponseRedirect(url)


@auth.election_admin_required
@auth.requires_election_features('delete_trustee')
@transaction.atomic
@require_http_methods(["POST"])
def trustee_delete(request, election, trustee_uuid):
    election.zeus.invalidate_election_public()
    trustee = election.trustees.get(uuid=trustee_uuid)
    trustee.delete()
    election.logger.info("Trustee %r deleted", trustee.email)
    election.zeus.compute_election_public()
    election.logger.info("Public key updated")
    url = election_reverse(election, 'trustees_list')
    return HttpResponseRedirect(url)


@auth.election_user_required
@require_http_methods(["GET"])
def index(request, election, poll=None):
    user = request.zeususer

    if poll:
        election_url = poll.get_absolute_url()
    else:
        election_url = election.get_absolute_url()

    booth_url = None
    linked_booth_urls = []
    if poll:
        booth_url = poll.get_booth_url(request)
        if poll.has_linked_polls and user.is_voter:
            for p in poll.linked_polls:
                if p == poll:
                    continue
                try:
                    voter = \
                        p.voters.get(voter_login_id=user._user.voter_login_id)
                except Exception as e:
                    continue
                burl = reverse('election_poll_voter_booth_linked_login',
                               args=(election.uuid, poll.uuid, voter.uuid,))
                burl = burl + "?link-to=%s" % p.uuid
                linked_booth_urls.append((p.name, burl,
                                          voter.cast_at))

    voter = None
    votes = None
    if user.is_voter:
        # cast any votes?
        voter = request.voter
        votes = voter.get_cast_votes()
        if election.frozen_at:
            voter.last_visit = datetime.datetime.now()
            voter.save()
        else:
            votes = None

    trustees = election.trustees.filter()

    context = {
        'election': election,
        'poll': poll,
        'trustees': trustees,
        'user': user,
        'votes': votes,
        'election_url': election_url,
        'booth_url': booth_url,
        'linked_booth_urls': linked_booth_urls
    }
    if poll:
        context['poll'] = poll

    set_menu('election', context)
    return render_template(request, 'election_view', context)


@auth.election_admin_required
@auth.requires_election_features('can_close_remote_mixing')
@require_http_methods(["POST"])
def close_mixing(request, election):
    election.logger.info("Closing remote mixes")

    election.remote_mixing_finished_at = datetime.datetime.now()
    election.save()

    tasks.election_validate_mixing(election.id)
    # hacky delay. Hopefully validate create task will start running
    # before the election view redirect.
    import time
    time.sleep(getattr(settings, 'ZEUS_ELECTION_FREEZE_DELAY', 4))
    url = election_reverse(election, 'index')
    return HttpResponseRedirect(url)


@auth.election_admin_required
@auth.requires_election_features('can_freeze')
@require_http_methods(["POST"])
def freeze(request, election):
    election.logger.info("Starting to freeze")
    tasks.election_validate_create(election.id)

    # hacky delay. Hopefully validate create task will start running
    # before the election view redirect.
    if not settings.CELERY_TASK_ALWAYS_EAGER:
        import time
        time.sleep(getattr(settings, 'ZEUS_ELECTION_FREEZE_DELAY', 4))

    url = election_reverse(election, 'index')
    return HttpResponseRedirect(url)


@auth.election_admin_required
@auth.requires_election_features('can_cancel')
@transaction.atomic
@require_http_methods(["POST"])
def cancel(request, election):

    cancel_msg = request.POST.get('cancel_msg', '')
    cancel_date = datetime.datetime.now()

    election.canceled_at = cancel_date
    election.cancelation_reason = cancel_msg
    election.completed_at = cancel_date

    election.save()
    url = election_reverse(election, 'index')
    return HttpResponseRedirect(url)


@auth.superadmin_required
@require_http_methods(["POST"])
def endnow(request, election):
    if election.voting_extended_until:
        election.voting_extended_until = datetime.datetime.now()
    else:
        election.voting_ends_at = datetime.datetime.now()
    election.save()
    election.logger.info("Changed election dates to be able to close voting")
    url = election_reverse(election, 'index')
    return HttpResponseRedirect(url)


@auth.election_admin_required
@auth.requires_election_features('can_close')
@require_http_methods(["POST"])
def close(request, election):
    election.close_voting()
    tasks.election_validate_voting(election.pk)
    url = election_reverse(election, 'index')
    return HttpResponseRedirect(url)


@auth.election_admin_required
@auth.requires_election_features('can_mix')
@require_http_methods(["POST"])
def start_mixing(request, election):
    tasks.start_mixing.delay(election_id=election.id)
    url = election_reverse(election, 'index')
    return HttpResponseRedirect(url)


@auth.election_admin_required
@auth.election_view()
@require_http_methods(["GET"])
def report(request, election, format):
    reports_list = request.GET.get('report',
                                   'election,voters,votes,results').split(",")

    _reports = OrderedDict()
    if 'election' in reports_list:
        _reports['election'] = list(reports.election_report([election],
                                                            True, False))
    if 'voters' in reports_list:
        _reports['voters'] = list(reports.election_voters_report([election]))
    if 'votes' in reports_list:
        _reports['votes'] = list(reports.election_votes_report([election],
                                                               True, True))
    if 'results' in reports_list:
        _reports['results'] = list(reports.election_results_report([election]))

    if format == "html":
        return render_template(request, "election_report", {
            'election': election,
            'reports': _reports,
        })
    else:
        def handler(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            raise TypeError

        return HttpResponse(json.dumps(_reports, default=handler),
                            content_type="application/json")


@auth.election_admin_required
@auth.requires_election_features('completed')
@require_http_methods(["GET"])
def public_stats(request, election):
    stats = {}
    stats['election'] = list(reports.election_report([election], True, True))
    stats['votes'] = list(reports.election_votes_report([election], True, True))
    stats['results'] = list(reports.election_results_report([election]))

    def handler(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        raise TypeError

    return HttpResponse(json.dumps(stats, default=handler),
                        content_type="application/json")


@auth.election_admin_required
@auth.requires_election_features('polls_results_computed')
@auth.allow_manager_access
@require_http_methods(["GET"])
def results_file(request, election, ext='pdf', shortname='',
                 language=settings.LANGUAGE_CODE):
    el_module = election.get_module()
    lang = language
    fpath = el_module.get_election_result_file_path(ext, ext, lang=lang)

    if not os.path.exists(fpath):
        election.compute_results_status = 'pending'
        election.save()
        election.compute_results()

    if request.GET.get('gen', None):
        election.compute_results_status = 'pending'
        election.save()
        election.compute_results()

    if not os.path.exists(fpath):
        raise Http404

    if settings.USE_X_SENDFILE:
        response = HttpResponse()
        response['Content-Type'] = ''
        response['X-Sendfile'] = fpath
        return response
    else:
        with open(fpath, "rb") as data:
            response = HttpResponse(data.read(), content_type='application/%s' % ext)
        basename = os.path.basename(fpath)
        response['Content-Disposition'] = 'attachment; filename=%s' % basename
        return response


@auth.superadmin_required
@auth.election_view()
@require_http_methods(["GET"])
def json_data(request, election):
    if not election.trial:
        raise PermissionDenied('33')
    election_json = serializers.serialize("json", [election])
    polls_json = serializers.serialize("json", election.polls.all())
    trustees_json = serializers.serialize("json", election.trustees.all())
    voters_json = serializers.serialize("json",
                                        Voter.objects.filter(poll__election=election))
    json = """{"election":%s, "polls": %s,
               "trustees": %s, "voters": %s}""" % (election_json,
                                                   polls_json,
                                                   trustees_json,
                                                   voters_json)
    return HttpResponse(json, content_type="application/json")


def test_cookie(request):
    continue_url = request.GET['continue_url']
    request.session.set_test_cookie()
    next_url = "%s?%s" % (reverse('test_cookie_2'),
                          six.moves.urllib.parse.urlencode({'continue_url': continue_url}))
    return HttpResponseRedirect(next_url)


def test_cookie_2(request):
    continue_url = request.GET['continue_url']

    if not request.session.test_cookie_worked():
        return HttpResponseRedirect("%s?%s" % (reverse('nocookies'),
                                               six.moves.urllib.parse.urlencode({
                                                   'continue_url':
                                                   continue_url})))

    request.session.delete_test_cookie()
    return HttpResponseRedirect(continue_url)


def nocookies(request):
    retest_url = "%s?%s" % (reverse('test_cookie'),
                            six.moves.urllib.parse.urlencode({
                            'continue_url': request.GET['continue_url']}))
    return render_template(request, 'nocookies', {'retest_url': retest_url})


@auth.election_view(check_access=False)
def remote_mix(request, election, mix_key):
    urls = []
    if not election.check_mix_key(mix_key):
        raise PermissionDenied

    urls = [p.remote_mix_url for p in election.polls.all()]
    return HttpResponse(json.dumps(urls), content_type="application/json")
