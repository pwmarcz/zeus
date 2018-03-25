import logging

from zeus import auth

logger = logging.getLogger()


class AuthenticationMiddleware(object):

    def process_request(self, request):
        setattr(request, 'zeususer', auth.ZeusUser(None))

        user = auth.ZeusUser.from_request(request)
        setattr(request, 'zeususer', user)
        if user.is_admin:
            setattr(request, 'admin', user._user)
        if user.is_voter:
            setattr(request, 'voter', user._user)
        if user.is_trustee:
            setattr(request, 'trustee', user._user)


class ExceptionsMiddleware(object):
    def process_exception(self, request, exception):
        logger.exception(exception)
