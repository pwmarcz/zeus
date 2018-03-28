
import datetime

from email.utils import formataddr
from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from helios.view_utils import render_template_raw
from django.db import transaction
from zeus import mobile

class ContactError(Exception):
    pass


class ContactBackend():

    Error = ContactError

    def __init__(self, logger, data=None):
        self.logger = logger
        self.data = data

    def can_notify(self, voter):
        raise NotImplemented

    def render_template(self, tpl, tpl_vars):
        return render_template_raw(None, tpl, tpl_vars)

    @staticmethod
    def should_fallback_to_email(poll, voter, methods):
        if len(methods) != 1 or 'sms' not in methods:
            return False

        sms_data = poll.election.sms_data
        sms_backend = SMSBackend(sms_data)
        if 'email' in voter.contact_methods and not sms_backend.can_notify(voter):
            return True
        return False

    @staticmethod
    def get_backend(method, logger, data=None):
        assert method in ['email', 'sms']
        if method == 'email':
            return EmailBackend(logger)
        if method == 'sms':
            return SMSBackend(logger, data=data)

    @staticmethod
    def notify_voter(poll, voter, id, methods, subjects, bodies, the_vars,
                     sent_hook=lambda x, y, z: x,
                     attachments=None, sender=None,
                     notify_once=False):

        logger = poll.logger

        if not notify_once and 'email' not in methods and ContactBackend.should_fallback_to_email(poll, voter, methods):
            logger.info("Fallback to email for voter %s", voter.voter_login_id)
            methods = ['email']

        notified = False
        for method in methods:
            if method not in voter.contact_methods:
                continue
            if notify_once and notified:
                continue
            assert method in subjects
            assert method in bodies
            data = None
            if method == 'sms':
                assert poll.election.sms_enabled
                data = poll.election.sms_data
            backend = ContactBackend.get_backend(method, logger, data)

            subject_tpl = subjects.get(method)
            body_tpl = bodies.get(method)
            subject = None
            if subject_tpl:
                subject = backend.render_template(subject_tpl, the_vars)
            body = backend.render_template(body_tpl, the_vars)
            backend.notify(voter, id, subject, body, attachments, sent_hook)
            notified = True

        if not notified:
            logger.error("Voter not notified %r" % (voter.voter_login_id))

    def notify(self, voter, id, subject, body, attachments, sent_hook):
        try:
            result, error = self.do_notify(voter, id, subject, body, attachments)
        except ContactBackend.Error as e:
            self.logger.exception(e)
            return False
        sent_hook(voter, result, error)


class EmailBackend(ContactBackend):

    def do_notify(self, voter, id, subject, body, attachments):
        self.logger.info("Notifying voter %r for '%r' via email (%r)" % (voter.voter_login_id, id, voter.voter_email))
        subject = subject.replace("\n", "")
        if attachments and len(attachments) > 0:
            name = "%s %s" % (voter.voter_name, voter.voter_surname)
            to = formataddr((name, voter.voter_email))
            message = EmailMessage(subject, body, settings.SERVER_EMAIL, [to])
            for attachment in attachments:
                message.attach(*attachment)
            try:
                return message.send(fail_silently=False), None
            except Exception as e:
                return None, e
        else:
            return voter.user.send_message(subject, body), None


class SMSBackend(ContactBackend):

    def get_data(self, update=False):
        # fresh data from db
        if update:
            return self.data.__class__.objects.select_for_update().get(pk=self.data.pk)
        else:
            return self.data.__class__.objects.get(pk=self.data.pk)

    def has_available_deliveries(self):
        data = self.get_data()
        return data.left > 0

    def can_notify(self, voter):
        return voter.voter_mobile and self.has_available_deliveries

    def do_notify(self, voter, id, subject, body, attachments):
        with transaction.atomic():
            data = self.get_data(update=True)
            if not self.has_available_deliveries():
                raise ContactBackend.Error("No sms deliveries available")
            self.logger.info("Notifying voter %r for '%s' via sms to '%s'" % (voter.voter_login_id, id, voter.voter_mobile))
            dlr_url = settings.SECURE_URL_HOST + reverse('election_poll_sms_delivery', args=(voter.poll.election.uuid, voter.poll.uuid))
            client = mobile.get_client(voter.poll.election, self.data, dlr_url=dlr_url)
            sent, error_or_code = client.send(voter.voter_mobile, body)
            msg_uid = client._last_uid

            if not sent:
                self.logger.error("SMS notification to voter '%s' failed (uid: %r, resp: %r)", voter.voter_login_id, msg_uid,
                                error_or_code)
            else:
                self.logger.info("SMS notification to voter '%s' sent (uid: %r, resp: %r)", msg_uid, msg_uid,
                                error_or_code)
            if sent:
                # store last notification date
                voter.last_sms_send_at = datetime.datetime.now()
                voter.last_sms_code = client.id + ":" + error_or_code
                if not client.remote_status:
                    voter.last_sms_status = 'sent'
                data.increase_sent(body)
            return sent, error_or_code if not sent else None
