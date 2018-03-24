"""
Generic Security -- for the auth system

Ben Adida (ben@adida.net)
"""

# nicely update the wrapper function


import uuid

from heliosauth.models import User

FIELDS_TO_SAVE = 'FIELDS_TO_SAVE'

# get the user


def get_user(request):
    # push the expiration of the session back
    # request.session.set_expiry(settings.SESSION_COOKIE_AGE)

    # set up CSRF protection if needed
    if not request.session.has_key('csrf_token') or type(request.session['csrf_token']) != str:
        request.session['csrf_token'] = str(uuid.uuid4())

    if request.session.has_key('user'):
        user = request.session['user']

        # find the user
        try:
            user_obj = User.get_by_type_and_id(user['type'], user['user_id'])
        except User.DoesNotExist:
            return None

        return user_obj
    else:
        return None
