
from django.urls import re_path
from zeus.views import site

urlpatterns = [
    re_path(r'^$', site.home, name='home'),
    re_path(r'^commit/$', site.commit, name='commit'),
    re_path(r'^stvcount/$', site.stv_count, name='stv_count'),
    re_path(r'^terms/$', site.terms, name='terms'),
    re_path(r'^faqs/$', site.faqs_voter, name='faqs'),
    re_path(r'^faqs/voter/$', site.faqs_voter, name='faqs_voter'),
    re_path(r'^faqs/trustee/$', site.faqs_trustee, name='faqs_trustee'),
    re_path(r'^resources/$', site.resources, name='site_resources'),
    re_path(r'^contact/$', site.contact, name='site_contact'),
    re_path(r'^stats/$', site.stats, name='site_stats'),
    re_path(r'^demo$', site.demo, name='site_demo'),
    re_path(r'^error/(?P<code>[0-9]+)$', site.error, name='error')
]
