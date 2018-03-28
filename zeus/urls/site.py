
from django.conf.urls import url
from zeus.views import site

urlpatterns = [
    url(r'^$', site.home, name='home'),
    url(r'^stvcount/$', site.stv_count, name='stv_count'),
    url(r'^terms/$', site.terms, name='terms'),
    url(r'^faqs/$', site.faqs_voter, name='faqs'),
    url(r'^faqs/voter/$', site.faqs_voter, name='faqs_voter'),
    url(r'^faqs/trustee/$', site.faqs_trustee, name='faqs_trustee'),
    url(r'^resources/$', site.resources, name='site_resources'),
    url(r'^contact/$', site.contact, name='site_contact'),
    url(r'^stats/$', site.stats, name='site_stats'),
    url(r'^demo$', site.demo, name='site_demo'),
    url(r'^error/(?P<code>[0-9]+)$', site.error, name='error')
]
