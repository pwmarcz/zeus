# -*- coding: utf-8 -*-

"""
Username/Password Authentication
"""


from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMessage


# some parameters to indicate that status updating is possible
STATUS_UPDATES = False


def update_status(token, message):
    pass


def send_message(user_id, user_name, user_info, subject, body, attachments=[]):
    email = user_id
    name = user_name or user_info.get('name', email)
    recipient = formataddr((name, email))
    message = EmailMessage(subject, body, settings.SERVER_EMAIL, [recipient])
    for attachment in attachments:
        message.attach(*attachment)

    message.send(fail_silently=False)
