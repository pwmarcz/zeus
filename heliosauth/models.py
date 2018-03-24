"""
Data Objects for user authentication

GAE

Ben Adida
(ben@adida.net)
"""

from django.db import models
from jsonfield import JSONField
from helios.fields import SeparatedValuesField


from auth_systems import AUTH_SYSTEMS

# an exception to catch when a user is no longer authenticated
class AuthenticationExpired(Exception):
    pass


def default_election_types_modules():
    from zeus.election_modules import ELECTION_MODULES_CHOICES
    return map(lambda s: s[0], ELECTION_MODULES_CHOICES)

def election_types_choices():
    from zeus.election_modules import ELECTION_MODULES_CHOICES
    return map(lambda s: (s[0], s[0]), ELECTION_MODULES_CHOICES)


class UserGroup(models.Model):
    name = models.CharField(max_length=255)
    election_types = SeparatedValuesField(max_length=255, default=default_election_types_modules)

    @property
    def election_types_display(self):
        return ",".join(self.election_types)

    @property
    def users_count_display(self):
        return self.user_set.count()

    def __unicode__(self):
        return self.name


class SMSBackendData(models.Model):

    credentials = models.TextField(max_length=255, null=True, default=None)
    limit = models.PositiveIntegerField(default=0)
    sent = models.PositiveIntegerField(default=0)
    sender = models.CharField(max_length=255, default="ZEUS")

    @property
    def left(self):
        return self.limit - self.sent

    def increase_sent(self, msg=None):
        inst = self.__class__.objects.get(pk=self.pk)
        inst.sent += 1
        inst.save()

    @property
    def display(self):
        return u"%s [%d/%d/%d]" % \
            (self.credentials, self.sent, self.limit, self.left)

class User(models.Model):
    user_type = models.CharField(max_length=50)
    user_id = models.CharField(max_length=100, unique=True)
    institution = models.ForeignKey('zeus.Institution', null=True)
    user_groups = models.ManyToManyField(UserGroup)
    name = models.CharField(max_length=200, null=True)

    # other properties
    info = JSONField()
    sms_data = models.ForeignKey(SMSBackendData, null=True, default=None)

    # access token information
    token = JSONField(null = True)

    @property
    def eligible_election_types(self):
        valid = set()
        for group in self.user_groups.all():
            map(valid.add, group.election_types)
        return valid

    # administrator
    admin_p = models.BooleanField(default=False)
    superadmin_p = models.BooleanField(default=False)
    management_p = models.BooleanField(default=False)
    ecounting_account = models.BooleanField(default=True)

    is_disabled = models.BooleanField(default=False)
    _is_authenticated = False

    class Meta:
        unique_together = (('user_type', 'user_id'),)

    @property
    def groups_display(self):
        return ",".join(map(lambda g: g.name, self.user_groups.filter()))

    @property
    def election(self):
        from helios.models import Election
        try:
            return self.elections.filter(archived_at=None)[0]
        except Election.DoesNotExist:
            return None
        except IndexError:
            return None

    @classmethod
    def _get_type_and_id(cls, user_type, user_id):
        return "%s:%s" % (user_type, user_id)

    @property
    def type_and_id(self):
        return self._get_type_and_id(self.user_type, self.user_id)

    @classmethod
    def get_by_type_and_id(cls, user_type, user_id):
        return cls.objects.get(user_type = user_type, user_id = user_id)

    @classmethod
    def update_or_create(cls, user_type, user_id, name=None, info=None, token=None):
        obj, created_p = cls.objects.get_or_create(user_type = user_type, user_id = user_id, defaults = {'name': name, 'info':info, 'token':token})

        if not created_p:
            # special case the password: don't replace it if it exists
            if obj.info.has_key('password'):
                info['password'] = obj.info['password']

            obj.info = info
            obj.name = name
            obj.token = token
            obj.save()

        return obj

    def is_authenticated(self):
        return self._is_authenticated == True

    def can_update_status(self):
        if not AUTH_SYSTEMS.has_key(self.user_type):
            return False

        return AUTH_SYSTEMS[self.user_type].STATUS_UPDATES

    def update_status_template(self):
        if not self.can_update_status():
            return None

        return AUTH_SYSTEMS[self.user_type].STATUS_UPDATE_WORDING_TEMPLATE

    def update_status(self, status):
        if AUTH_SYSTEMS.has_key(self.user_type):
            AUTH_SYSTEMS[self.user_type].update_status(self.user_id, self.info, self.token, status)

    def send_message(self, subject, body, attachments=[]):
        if AUTH_SYSTEMS.has_key(self.user_type):
            subject = subject.split("\n")[0]
            AUTH_SYSTEMS[self.user_type].send_message(self.user_id, self.name,
                                                      self.info, subject, body,
                                                      attachments=attachments)

    def send_notification(self, message):
        if AUTH_SYSTEMS.has_key(self.user_type):
            if hasattr(AUTH_SYSTEMS[self.user_type], 'send_notification'):
                AUTH_SYSTEMS[self.user_type].send_notification(self.user_id, self.info, message)

    def is_eligible_for(self, eligibility_case):
        """
        Check if this user is eligible for this particular eligibility case, which looks like
        {'auth_system': 'cas', 'constraint': [{}, {}, {}]}
        and the constraints are OR'ed together
        """

        if eligibility_case['auth_system'] != self.user_type:
            return False

        # no constraint? Then eligible!
        if not eligibility_case.has_key('constraint'):
            return True

        # from here on we know we match the auth system, but do we match one of the constraints?

        auth_system = AUTH_SYSTEMS[self.user_type]

        # does the auth system allow for checking a constraint?
        if not hasattr(auth_system, 'check_constraint'):
            return False

        for constraint in eligibility_case['constraint']:
            # do we match on this constraint?
            if auth_system.check_constraint(constraint=constraint, user = self):
                return True

        # no luck
        return False

    def __eq__(self, other):
        if other:
            return self.type_and_id == other.type_and_id
        else:
            return False

    @property
    def pretty_name(self):
        if self.name:
            return self.name

        if self.info.has_key('name'):
            return self.info['name']

        return self.user_id

    @property
    def public_url(self):
        if AUTH_SYSTEMS.has_key(self.user_type):
            if hasattr(AUTH_SYSTEMS[self.user_type], 'public_url'):
                return AUTH_SYSTEMS[self.user_type].public_url(self.user_id)

        return None

    def _display_html(self, size):
        public_url = self.public_url

        if public_url:
            name_display = '<a href="%s">%s</a>' % (public_url, self.pretty_name)
        else:
            name_display = self.pretty_name

        return """%s""" % (
          str(name_display), )

    @property
    def display_html_small(self):
        return self._display_html(15)

    @property
    def display_html_big(self):
        return self._display_html(25)
