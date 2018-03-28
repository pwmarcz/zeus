
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404

from helios.view_utils import render_template
from heliosauth.models import User, UserGroup
from django.contrib.auth.hashers import make_password
from zeus.models.zeus_models import Institution
from zeus.auth import manager_or_superadmin_required, superadmin_required
from account_administration.forms import userForm, institutionForm, userGroupForm
from .utils import random_password, can_do, sanitize_get_param, \
    get_user, get_institution


@manager_or_superadmin_required
def list_users(request):
    users = User.objects.all()
    users = users.order_by('id')
    # filtering
    inst = request.GET.get('inst')
    if inst:
        users = users.filter(institution__name__icontains=inst)
    uid = request.GET.get('uid')
    if uid:
        users = users.filter(user_id__icontains=uid)
    context = {
        'paginate_by': 10,
        'users': users,
        'inst': inst,
        'uid': uid,
        }
    return render_template(
        request,
        'account_administration/list_users',
        context
        )

@manager_or_superadmin_required
def list_institutions(request):
    institutions = Institution.objects.all()
    institutions = institutions.order_by('id')
    #filtering
    inst_name = request.GET.get('inst_name')
    if inst_name:
        institutions = institutions.filter(name__icontains=inst_name)
    context = {
        'paginate_by': 10,
        'inst_name': inst_name,
        'institutions': institutions,
        'request': request
    }
    return render_template(
        request,
        'account_administration/list_institutions',
        context)


@superadmin_required
def list_usergroups(request):
    groups = UserGroup.objects.filter().order_by('name')
    context = {'paginate_by': 10, 'groups': groups}
    return render_template(request, 'account_administration/list_usergroups',
                           context)


@manager_or_superadmin_required
def create_user(request):
    users = User.objects.all()
    inst_id = sanitize_get_param(request.GET.get('id'))
    institution = get_institution(inst_id)
    edit_id = sanitize_get_param(request.GET.get('edit_id'))
    edit_user = get_user(edit_id)
    logged_user = request.zeususer._user
    if edit_user:
        if not can_do(logged_user, edit_user):
            raise PermissionDenied
    if edit_user:
        initial = {'institution': edit_user.institution.name}
    elif institution:
        initial = {'institution': institution.name}
    else:
        initial = None
    form = None

    if request.method == 'POST':
        form = userForm(logged_user, request.POST, initial=initial, instance=edit_user)
        if form.is_valid():
            user, password = form.save()
            if edit_user:
                message = _("Changes on user were successfully saved")
            else:
                message = _("User %(uid)s was created with"
                            " password %(password)s.")\
                            % {'uid': user.user_id, 'password': password}
            messages.success(request, message)
            url = "%s?uid=%s" % (reverse('user_management'), \
                str(user.id))
            return redirect(url)

    if request.method == 'GET':
        form = userForm(logged_user, initial=initial, instance=edit_user)

    tpl = 'account_administration/create_user',
    context = {'form': form}
    return render_template(request, tpl, context)

@manager_or_superadmin_required
def create_institution(request):
    inst_id = sanitize_get_param(request.GET.get('id'))
    edit_inst = get_institution(inst_id)
    form = None
    if request.method == 'POST':
        form = institutionForm(request.POST, instance=edit_inst)
        if form.is_valid():
            form.save()
            if edit_inst:
                message = _("Changes were successfully saved")
            else:
                message= _("Institution created.")
            messages.success(request, message)
            return redirect(reverse('list_institutions'))
    if request.method == 'GET':
        form = institutionForm(instance=edit_inst)
    context = {'form': form}
    return render_template(
        request,
        'account_administration/create_institution',
        context
        )

@superadmin_required
def create_usergroup(request):
    groups = UserGroup.objects.all()
    edit_id = sanitize_get_param(request.GET.get('edit_id'))
    edit_group = None
    if edit_id:
        edit_group = get_object_or_404(UserGroup, id=edit_id)
    logged_user = request.zeususer._user
    if request.method == 'POST':
        form = userGroupForm(request.POST, instance=edit_group)
        if form.is_valid():
            group = form.save()
            if edit_group:
                message = _("Changes on user group were successfully saved")
            else:
                message = _("Group %s was created" % (group.name))
            messages.success(request, message)
            url = reverse('list_usergroups')
            return redirect(url)

    if request.method == 'GET':
        form = userGroupForm(instance=edit_group)

    tpl = 'account_administration/create_usergroup',
    context = {'form': form}
    return render_template(request, tpl, context)

@manager_or_superadmin_required
def manage_user(request):
    users = User.objects.all()
    uid = request.GET.get('uid')
    uid = sanitize_get_param(uid)

    if request.zeususer._user.management_p:
        user_type = 'manager'
    if request.zeususer._user.superadmin_p:
        user_type = 'superadmin'
    user = get_user(uid)
    if not user:
        message = _("You didn't choose a user")
        messages.error(request, message)
    context = {'u_data': user, 'user_type': user_type}
    return render_template(
        request,
        'account_administration/user_manage',
        context)

@manager_or_superadmin_required
def reset_password(request):
    uid = request.GET.get('uid')
    uid = sanitize_get_param(uid)
    user = get_user(uid)
    context = {"u_data": user}
    return render_template(
        request,
        'account_administration/reset_password',
        context)

@manager_or_superadmin_required
def reset_password_confirmed(request):
    uid = request.GET.get('uid')
    uid = sanitize_get_param(uid)
    logged_user = request.zeususer._user
    user = get_user(uid)
    if user:
        if can_do(logged_user, user):
            new_password = random_password()
            user.info['password'] = make_password(new_password)
            user.save()
            message = _("New password for user %(uid)s is "
                        "%(new_pass)s") % {'uid': user.user_id,
                                           'new_pass': new_password}
            messages.info(request, message)
        else:
            message = _("You are not authorized to do this")
            messages.error(request, message)
    else:
        message = _("You didn't choose a user")
        messages.error(request, message)
        return redirect(reverse('list_users'))
    url = "%s?uid=%s" % (reverse('user_management'),
                                   str(user.id))
    return redirect(url)
