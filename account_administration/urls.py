
from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^$', views.list_users,
        name='list_users'),
    re_path(r'^user_list/$', views.list_users,
        name='list_users'),
    re_path(r'^group_creation/$', views.create_usergroup,
        name='create_usergroup'),
    re_path(r'^user_creation/$', views.create_user,
        name='create_user'),
    re_path(r'^institution_creation/$',
        views.create_institution,
        name='create_institution'),
    re_path(r'usergroup_list/$',
        views.list_usergroups,
        name='list_usergroups'),
    re_path(r'institution_list/$',
        views.list_institutions,
        name='list_institutions'),
    re_path(r'user_management/$',
        views.manage_user,
        name='user_management'),
    re_path(r'reset_password/$',
        views.reset_password,
        name='reset_password'),
    re_path(r'reset_password_confirmed/$',
        views.reset_password_confirmed,
        name='reset_password_confirmed'),
]
