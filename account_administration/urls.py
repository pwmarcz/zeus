from __future__ import absolute_import
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.list_users,
        name='list_users'),
    url(r'^user_list/$', views.list_users,
        name='list_users'),
    url(r'^group_creation/$', views.create_usergroup,
        name='create_usergroup'),
    url(r'^user_creation/$', views.create_user,
        name='create_user'),
    url(r'^institution_creation/$',
        views.create_institution,
        name='create_institution'),
    url(r'usergroup_list/$',
        views.list_usergroups,
        name='list_usergroups'),
    url(r'institution_list/$',
        views.list_institutions,
        name='list_institutions'),
    url(r'user_management/$',
        views.manage_user,
        name='user_management'),
    url(r'reset_password/$',
        views.reset_password,
        name='reset_password'),
    url(r'reset_password_confirmed/$',
        views.reset_password_confirmed,
        name='reset_password_confirmed'),
]
