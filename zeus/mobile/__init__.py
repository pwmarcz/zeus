import os
import datetime
import logging

from collections import defaultdict
from django.conf import settings

from zeus.mobile import locotel, mybsms

logger = logging.getLogger(__name__)

class FileClient():

    location = getattr(settings, 'SMS_FILE_LOCATION', '/tmp')
    id = "fake"
    remote_status = False

    def __init__(self, from_mobile, user, password, dlr_url):
        self.user = user
        self.password = password
        self.from_mobile = from_mobile
        self.delivery_url = dlr_url
        assert self.delivery_url

    def send(self, mobile, msg, fields={}, uid=None):
        fname = "sms-" + datetime.datetime.now().isoformat() + "-" + mobile.replace("+", "")
        f = file(os.path.join(self.location, fname), "w")
        f.write(msg)
        f.close()
        self._last_uid = fname
        return True, fname

def get_client(election, data, **kwargs):

    username, password = data.credentials.split(":")
    sender = data.sender or "ZEUS"
    logger.info("Using sms api credentials for election %r: %r" % (
        election.uuid,
        {
            'username': username,
            'sender': sender
        }
    ))
    if settings.SMS_BACKEND == 'file':
        return FileClient(sender, username, password, **kwargs)
    return mybsms.Client(sender, username, password, **kwargs)
