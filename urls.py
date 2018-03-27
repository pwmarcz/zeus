# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import include, url
from django.conf import settings
import django.views.i18n
import django.views.static

from zeus.views import auth, admin, poll, site, shared

SERVER_PREFIX = getattr(settings, 'SERVER_PREFIX', '')
if SERVER_PREFIX:
    SERVER_PREFIX = SERVER_PREFIX.rstrip('/') + '/'

app_patterns = []

auth_urls = [
    url(r'^auth/logout', auth.logout, name='logout'),
    url(r'^auth/login', auth.password_login_view, name='login'),
    url(r'^auth/change_password', auth.change_password, name='change_password'),
    url(r'^voter-login$', auth.voter_login, name="voter_login"),
    url(r'^auth/oauth2$', auth.oauth2_login, name="oauth2_login"),
    url(r'^auth/jwt$', auth.jwt_login, name="jwt_login"),
    url(r'^auth/shibboleth/(?P<endpoint>.*)$', auth.shibboleth_login, name="shibboleth_login"),
]

admin_urls = [
    url(r'^$', admin.HomeView.as_view(), name='admin_home'),
    url(r'^reports$', admin.elections_report, name='elections_report'),
    url(r'^reports/csv$', admin.elections_report_csv, name='elections_report_csv'),
]

app_patterns += [
    url(r'^vote', auth.voter_login, name='voter_quick_login'),
    url(r'^f/(?P<fingerprint>.*)', poll.download_signature_short, name='download_signature_short'),
    url(r'^', include('zeus.urls.site')),
    url(r'^elections/', include('zeus.urls.election')),
    url(r'^auth/', include(auth_urls)),
    url(r'^admin/', include(admin_urls)),
    url(r'^get-randomness/', shared.get_randomness,
        name="get_randomness"),
    url(r'^i18n/js', django.views.i18n.javascript_catalog,
        name='js_messages', kwargs={'packages': None}),
    url(r'^i18n/setlang', site.setlang),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^account_administration/', include('account_administration.urls')),
]

urlpatterns = [
    url(r'^' + SERVER_PREFIX, include(app_patterns)),
]

#SHOULD BE REPLACED BY APACHE STATIC PATH
if getattr(settings, 'DEBUG', False) or getattr(settings, 'ZEUS_SERVE_STATIC', False):
    static_urls = [
        url(r'booth/(?P<path>.*)$', django.views.static.serve, {
            'document_root' : settings.BOOTH_STATIC_PATH
        }),
        url(r'static/zeus/(?P<path>.*)$', django.views.static.serve, {
            'document_root' : settings.ROOT_PATH + '/zeus/static/zeus'
        }),
        url(r'static/(?P<path>.*)$', django.views.static.serve, {
            'document_root' : settings.ROOT_PATH + '/server_ui/media'
        }),
    ]

    urlpatterns += static_urls

handler500 = 'zeus.views.site.handler500'
handler400 = 'zeus.views.site.handler400'
handler403 = 'zeus.views.site.handler403'
handler404 = 'zeus.views.site.handler404'
