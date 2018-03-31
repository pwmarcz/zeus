
import copy
import datetime
import logging

from functools import wraps

from helios.models import Election, Voter, Poll

from django.urls import reverse
from django.utils import translation
from django.conf import settings
from django.db import transaction

from zeus import mobile
from zeus import utils
from zeus.contact import ContactBackend
from zeus.celery import app


logger = logging.getLogger(__name__)


def task(*taskargs, **taskkwargs):
    """
    Task helper to automatically initialize django mechanism using the
    default language set in project settings.
    """
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            prev_language = translation.get_language()
            if prev_language != settings.LANGUAGE_CODE:
                translation.activate(settings.LANGUAGE_CODE)
            return func(*args, **kwargs)
        # prevent magic kwargs passthrough
        if 'accept_magic_kwargs' not in taskkwargs:
            taskkwargs['accept_magic_kwargs'] = False
        return app.task(*taskargs, **taskkwargs)(inner)
    return wrapper


def poll_task(*taskargs, **taskkwargs):
    def wrapper(func):
        #if not 'rate_limit' in taskkwargs:
            #taskkwargs['rate_limit'] = '5/m'
        return task(*taskargs, **taskkwargs)(func)
    return wrapper


@task(rate_limit=getattr(settings, 'ZEUS_VOTER_EMAIL_RATE', '20/m'),
      ignore_result=True)
def single_voter_email(voter_uuid,
                       contact_methods,
                       contact_id,
                       subject_template_email,
                       body_template_email,
                       body_template_sms,
                       template_vars={},
                       update_date=True,
                       update_booth_invitation_date=False,
                       notify_once=False):

    voter = Voter.objects.get(uuid=voter_uuid)
    lang = voter.poll.election.communication_language

    with translation.override(lang):
        template_vars= copy.copy(template_vars)
        template_vars.update({'voter': voter, 'poll': voter.poll,
                              'election': voter.poll.election})

        subject_tpls = {
            'email': subject_template_email,
            'sms': ''
        }

        body_tpls = {
            'email': body_template_email,
            'sms': body_template_sms
        }

        def sent_hook(voter, method, error=None):
            if error:
                return
            linked_voters = voter.linked_voters
            if method == 'email' and update_date:
                for voter in linked_voters:
                    voter.last_email_send_at = datetime.datetime.now()
                    voter.save()
            if method == 'sms' and update_date:
                for voter in linked_voters:
                    voter.last_sms_send_at = datetime.datetime.now()
                    voter.save()
            if update_booth_invitation_date:
                for voter in linked_voters:
                    voter.last_booth_invitation_send_at = datetime.datetime.now()
                    voter.save()

        ContactBackend.notify_voter(
            voter.poll,
            voter,
            contact_id,
            contact_methods,
            subject_tpls,
            body_tpls,
            template_vars,
            sent_hook=sent_hook,
            notify_once=notify_once)


@task(ignore_result=True)
def voters_email(poll_id,
                 contact_methods,
                 contact_id,
                 subject_template_email,
                 body_template_email,
                 body_template_sms,
                 template_vars={},
                 voter_constraints_include=None,
                 voter_constraints_exclude=None,
                 update_date=True,
                 update_booth_invitation_date=False,
                 notify_once=False,
                 q_param=None):

    poll = Poll.objects.get(id=poll_id)
    voters = poll.voters.filter(utils.get_voters_filters_with_constraints(
        q_param, voter_constraints_include, voter_constraints_exclude
    ))

    poll.logger.info("Notifying %d voters via %r" % (voters.count(), contact_methods))
    if len(poll.linked_polls) > 1 and 'vote_body' in body_template_email:
        body_template_email = body_template_email.replace("_body.txt", "_linked_body.txt")
        #TODO: Handle linked polls sms notification

    for voter in voters:
        single_voter_email.delay(voter.uuid,
                                 contact_methods,
                                 contact_id,
                                 subject_template_email,
                                 body_template_email,
                                 body_template_sms,
                                 template_vars,
                                 update_date,
                                 update_booth_invitation_date,
                                 notify_once=notify_once)


@task(rate_limit=getattr(settings, 'ZEUS_VOTER_EMAIL_RATE', '20/m'),
      ignore_result=True)
def send_cast_vote_email(poll_pk, voter_pk, signature, fingerprint):
    poll = Poll.objects.get(pk=poll_pk)
    election = poll.election
    lang = election.communication_language
    voter = poll.voters.filter().get(pk=voter_pk)

    with translation.override(lang):
        email_subject = "email/cast_done_subject.txt"
        email_body = "email/cast_done_body.txt"
        sms_body = "sms/cast_done_body.txt"
        # send it via the notification system associated with the auth system
        attachments = [('vote.signature', signature['signature'], 'text/plain')]

        subject_tpls = {
            'email': email_subject,
            'sms': None
        }

        body_tpls = {
            'email': email_body,
            'sms': sms_body
        }

        receipt_url = settings.SECURE_URL_HOST + reverse('download_signature_short', args=(fingerprint,))
        tpl_vars = {
            'voter': voter,
            'poll': poll,
            'election': election,
            'signature': signature,
            'date': voter.last_cast_vote().cast_at,
            'vote_receipt_url': receipt_url
        }
        ContactBackend.notify_voter(
            poll, voter, 'cast_done', voter.contact_methods, subject_tpls,
            body_tpls, tpl_vars, attachments=attachments,
            notify_once=election.cast_notify_once)


@poll_task(ignore_result=True)
def poll_validate_create(poll_id):
    poll = Poll.objects.get(id=poll_id)
    poll.validate_create()


@task(ignore_result=True)
def election_validate_create(election_id):
    with transaction.atomic():
        election = Election.objects.select_for_update().get(id=election_id)
        election.logger.info("Spawning validate create poll tasks")
        if election.polls_feature_frozen:
            election.frozen_at = datetime.datetime.now()
            election.save()

    for poll in election.polls.all():
        if not poll.feature_can_validate_create:
            poll_validate_create.delay(poll.id)

    subject = "Election is frozen"
    msg = "Election is frozen"
    msg = utils.append_ballot_to_msg(election, msg)
    election.notify_admins(msg=msg, subject=subject)


@task(ignore_result=True)
def election_validate_voting(election_id):
    election = Election.objects.get(pk=election_id)
    election.logger.info("Spawning validate voting poll tasks")
    for poll in election.polls.all():
        if poll.feature_can_validate_voting:
            poll_validate_voting.delay(poll.pk)


@poll_task(ignore_result=True)
def poll_validate_voting(poll_id):
    poll = Poll.objects.get(pk=poll_id)
    poll.validate_voting()
    if poll.election.polls_feature_validate_voting_finished:
        subject = "Validate voting finished"
        msg = "Validate voting finished"
        poll.election.notify_admins(msg=msg, subject=subject)
        election_mix.delay(poll.election.pk)


@task(ignore_result=True)
def election_mix(election_id):
    election = Election.objects.get(pk=election_id)
    election.logger.info("Spawning mix poll tasks")
    for poll in election.polls.all():
        if poll.feature_can_mix:
            poll_mix.delay(poll.pk)


@poll_task(ignore_result=True)
def poll_mix(poll_id):
    poll = Poll.objects.get(pk=poll_id)
    poll.mix()
    if poll.election.polls_feature_mixing_finished:
        subject = "Mixing finished"
        msg = "Mixing finished"
        poll.election.notify_admins(msg=msg, subject=subject)
        election_validate_mixing.delay(poll.election.pk)


@task(ignore_result=True)
def election_validate_mixing(election_id):
    election = Election.objects.get(pk=election_id)
    election.logger.info("Spawning validate mix poll tasks")
    for poll in election.polls.all():
        if poll.feature_can_validate_mixing:
            poll_validate_mixing.delay(poll.pk)


@poll_task(ignore_result=True)
def poll_validate_mixing(poll_id):
    poll = Poll.objects.get(pk=poll_id)
    poll.validate_mixing()
    if poll.election.polls_feature_validate_mixing_finished:
        subject = "Validate mixing finished"
        msg = "Validate mixing finished"
        poll.election.notify_admins(msg=msg, subject=subject)
        election_zeus_partial_decrypt.delay(poll.election.pk)


@task(ignore_result=True)
def notify_trustees(election_id):
    election = Election.objects.get(pk=election_id)
    for trustee in election.trustees.filter().no_secret():
        trustee.send_url_via_mail()


@task(ignore_result=True)
def election_zeus_partial_decrypt(election_id):
    election = Election.objects.get(pk=election_id)
    election.logger.info("Spawning zeus partial decrypt poll tasks")
    notify_trustees.delay(election.pk)
    for poll in election.polls.all():
        if poll.feature_can_zeus_partial_decrypt:
            poll_zeus_partial_decrypt.delay(poll.pk)


@poll_task(ignore_result=True)
def poll_zeus_partial_decrypt(poll_id):
    poll = Poll.objects.get(pk=poll_id)
    poll.zeus_partial_decrypt()
    if poll.election.trustees.filter().no_secret().count() == 0:
        poll.partial_decrypt_started_at = datetime.datetime.now()
        poll.partial_decrypt_finished_at = datetime.datetime.now()
        poll.save()
    if poll.election.polls_feature_partial_decryptions_finished:
        election_decrypt.delay(poll.election.pk)


@poll_task(ignore_result=True)
def poll_add_trustee_factors(poll_id, trustee_id, factors, proofs):
    poll = Poll.objects.get(pk=poll_id)
    trustee = poll.election.trustees.get(pk=trustee_id)
    poll.partial_decrypt(trustee, factors, proofs)
    if poll.election.polls_feature_partial_decryptions_finished:
        election_decrypt.delay(poll.election.pk)


@task(ignore_result=True)
def election_decrypt(election_id):
    election = Election.objects.get(pk=election_id)
    election.logger.info("Spawning decrypt poll tasks")
    subject = "Trustees partial decryptions finished"
    msg = "Trustees partial decryptions finished"
    election.notify_admins(msg=msg, subject=subject)
    for poll in election.polls.all():
        if poll.feature_can_decrypt:
            poll_decrypt.delay(poll.pk)


@poll_task(ignore_result=True)
def poll_decrypt(poll_id):
    poll = Poll.objects.get(pk=poll_id)
    poll.decrypt()
    if poll.election.polls_feature_decrypt_finished:
        subject = "Decryption finished"
        msg = "Decryption finished"
        poll.election.notify_admins(msg=msg, subject=subject)
        election_compute_results.delay(poll.election.pk)


@task(ignore_result=True)
def election_compute_results(election_id):
    election = Election.objects.get(pk=election_id)
    election.logger.info("Spawning compute results poll tasks")
    for poll in election.polls.all():
        if poll.feature_can_compute_results:
            poll_compute_results.delay(poll.pk)


@poll_task(ignore_result=True)
def poll_compute_results(poll_id):
    poll = Poll.objects.get(pk=poll_id)
    poll.compute_results()
    if poll.election.polls_feature_compute_results_finished:
        e = poll.election
        e.completed_at = datetime.datetime.now()
        e.save()
        e.compute_results()
        subject = "Results computed - docs generated"
        msg = "Results computed - docs generated"
        e.notify_admins(msg=msg, subject=subject)


@task(ignore_result=False)
def check_sms_status(voter_id, code, election_uuid=None):
    voter = Voter.objects.select_related().get(pk=voter_id)
    if voter.last_sms_status:
        return voter.last_sms_status

    client = mobile.get_client(election_uuid)
    return client.status(code)
