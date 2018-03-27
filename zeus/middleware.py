from __future__ import absolute_import
import logging

from zeus import auth

logger = logging.getLogger()


def AuthenticationMiddleware(get_response):

    def middleware(request):
        setattr(request, 'zeususer', auth.ZeusUser(None))

        user = auth.ZeusUser.from_request(request)
        setattr(request, 'zeususer', user)
        if user.is_admin:
            setattr(request, 'admin', user._user)
        if user.is_voter:
            setattr(request, 'voter', user._user)
        if user.is_trustee:
            setattr(request, 'trustee', user._user)

        return get_response(request)

    return middleware


# TODO is this necessary?
class ExceptionsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.exception(exception)
