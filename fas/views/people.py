# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Xavier Lamien.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# __author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.security import NO_PERMISSION_REQUIRED

import fas.models.provider as provider
import fas.models.register as register

from fas.security import generate_token
from fas.security import PasswordValidator

from fas.forms.people import EditPeopleForm
from fas.forms.people import UpdateStatusForm
from fas.forms.people import UpdatePasswordForm
from fas.forms.people import UsernameForm
from fas.forms.people import ResetPasswordPeopleForm
from fas.forms.people import UpdateAvatarForm
from fas.forms.people import UpdateSshKeyForm
from fas.forms.people import UpdateGpgFingerPrint
from fas.forms.captcha import CaptchaForm
from fas.forms.account import AccountPermissionForm

from fas.util import compute_list_pages_from
from fas.lib.avatar import gen_libravatar
from fas.models.group import MembershipStatus
from fas.models.people import AccountStatus, AccountPermissionType, AccountLogType
from fas.events import PasswordChangeRequested, PeopleInfosUpdated, \
    NotificationRequest
from fas.views import redirect_to


from pyramid.httpexceptions import HTTPNotFound

import GeoIP
import logging
from fas.util import _, Config

log = logging.getLogger(__name__)


class People(object):
    def __init__(self, request):
        self.request = request
        self.id = -1
        self.person = None
        self.notify = self.request.registry.notify

    @view_config(route_name='people', renderer='/people/list.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    @view_config(route_name='people-paging', renderer='/people/list.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    def paging(self):
        """ People list's view with paging. """
        try:
            page = int(self.request.matchdict.get('pagenb', 1))
        except ValueError:
            return HTTPBadRequest('No page number specified')

        # TODO: get limit from config file or let user choose in between
        # predefined one ?
        people = provider.get_people(50, page)
        peoples = provider.get_people(count=True)

        pages = compute_list_pages_from(peoples, 50)

        if page > pages:
            return HTTPBadRequest(
                'The page is bigger than the maximum number of pages')

        return dict(
            people=people,
            count=int(peoples),
            page=page,
            pages=pages
        )

    @view_config(route_name='people-search-rd')
    def search_redirect(self):
        """ Redirects the search to the proper url. """
        query = self.request.params.get('q', '*')

        return redirect_to(self.request, 'people-search', pattern=query)

    @view_config(route_name='people-search', renderer='/people/list.xhtml')
    @view_config(route_name='people-search-paging', renderer='/people/list.xhtml')
    def search(self):
        """ Search people page. """
        try:
            _id = self.request.matchdict['pattern']
        except KeyError:
            return HTTPBadRequest('No pattern specified')
        page = int(self.request.matchdict.get('pagenb', 1))

        username = None
        try:
            _id = int(_id)
        except ValueError:
            username = _id

        if username:
            if '*' in username:
                username = username.replace('*', '%')
            else:
                username += '%'
            people = provider.get_people(50, page, pattern=username)
            peoples = provider.get_people(pattern=username, count=True)
        else:
            people = provider.get_people_by_id(_id)
            peoples = 1

        if not people:
            self.request.session.flash(
                _('No user found for the query: %s' % _id), 'error')
            return redirect_to(self.request, 'people')

        pages = compute_list_pages_from(peoples, 50)

        if page > pages:
            return HTTPBadRequest(
                'The page is bigger than the maximum number of pages')

        if username and len(people) == 1 and page == 1:
            self.request.session.flash(
                _("Only one user matching, redirecting to the user's page"),
                'info')
            return redirect_to(self.request, 'people-profile', id=people[0].id)

        return dict(
            people=people,
            page=page,
            pages=pages,
            count=int(peoples),
            pattern=_id,
            display_username=True
        )

    @view_config(route_name='people-profile', renderer='/people/profile.xhtml')
    def profile(self):
        """ People profile page. """
        try:
            _id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest('No id specified')

        username = None
        try:
            _id = int(_id)
        except ValueError:
            username = _id

        if username:
            self.person = provider.get_people_by_username(username)
        else:
            self.person = provider.get_people_by_id(_id)

        if not self.person:
            raise HTTPNotFound('No such user found')

        if not self.request.authenticated_is_admin():
            if self.person.status not in [
                AccountStatus.ACTIVE,
                AccountStatus.INACTIVE,
                AccountStatus.ON_VACATION]:
                return redirect_to(self.request, 'people')

        form_avatar = UpdateAvatarForm(self.request.POST, self.person)
        form = UpdateStatusForm(self.request.POST, self.person)
        form_sshkey = UpdateSshKeyForm(self.request.POST, self.person)
        form_gpgfp = UpdateGpgFingerPrint(self.request.POST, self.person)

        if self.request.get_user:
            if self.request.get_user.username == self.person.username:
                form.status.choices = [
                    (s.value, s.name.lower()) for s in AccountStatus
                    if s in [
                        AccountStatus.ACTIVE,
                        AccountStatus.INACTIVE,
                        AccountStatus.ON_VACATION,
                        AccountStatus.DISABLED
                    ]
                ]

        if self.request.method == 'POST':
            if form.validate():
                log.debug(
                    'Updating person status to: %s',
                    form.status.data)
                form.populate_obj(self.person)
            if form_avatar.validate():
                log.debug(
                    'Updating avatar id to: %s',
                    form_avatar.avatar_id.data)
                self.person.avatar = gen_libravatar(
                    form_avatar.avatar_id.data)
                form_avatar.populate_obj(self.person)
            if form_sshkey.validate():
                form_sshkey.populate_obj(self.person)
            if form_gpgfp.validate():
                form_gpgfp.populate_obj(self.person)

        membership = [
            g for g in self.person.group_membership
            if not g.status == MembershipStatus.PENDING
            ]

        ssh_is_required = False
        for g in membership:
            if g.group and g.group.requires_ssh:
                ssh_is_required = True

        return dict(
            person=self.person,
            form=form,
            formavatar=form_avatar,
            formsshkey=form_sshkey,
            form_gpgfp=form_gpgfp,
            membership=membership,
            ssh_is_required=ssh_is_required,
            account_status=AccountStatus,
        )

    @view_config(route_name='people-activities',
                 renderer='/people/activities.xhtml')
    def activities(self):
        """ People's activities page. """
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest('No id specified')

        activities = provider.get_account_activities_by_people_id(self.id)

        # Prevent client/user from requesting direct url
        if len(activities) > 0:
            self.person = activities[0].person
            if self.request.authenticated_userid != self.person.username:
                return redirect_to(self.request, 'people-profile', id=self.id)
        else:
            if self.request.authenticated_userid != self.person.username \
                    or self.request.authenticated_userid == \
                            self.person.username:
                return redirect_to(self.request, 'people-profile', id=self.id)

        return dict(activities=activities, person=self.person)

    @view_config(route_name='people-edit', permission='authenticated',
                 renderer='/people/edit-infos.xhtml')
    def edit(self):
        """ Profile's edit page."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest('No id specified')

        username = None
        try:
            self.id = int(self.id)
        except:
            username = self.id

        if username:
            self.person = provider.get_people_by_username(username)
        else:
            self.person = provider.get_people_by_id(self.id)

        if not self.person:
            raise HTTPNotFound('No such user found')

        # TODO: move this to Auth provider?
        if self.request.authenticated_userid != self.person.username:
            return redirect_to(self.request, 'people-profile', id=self.id)

        form = EditPeopleForm(self.request.POST, self.person)

        # Remove fields we don't need for this form'
        del form.status
        del form.ssh_key
        del form.blog_rss
        del form.facsimile
        del form.affiliation
        del form.avatar

        # username is not edit-able
        form.username.data = self.person.username

        form.country_code.choices = [
            (c[0], '%s (%s)' % (unicode(c[1]), c[0]))
            for c in GeoIP.country_names.iteritems()
            if c[0] not in Config.get('blacklist.country')]

        form.locale.choices = [
            (l, l) for l in list(Config.get('locale.available', '').split(','))]

        if self.request.method == 'POST' \
                and ('form.save.person-infos' in self.request.params):
            if form.validate():
                form.populate_obj(self.person)
                self.notify(PeopleInfosUpdated(self.request, form, self.person))

                return redirect_to(self.request, 'people-profile', id=self.id)

        return dict(form=form, id=self.id)

    @view_config(route_name='lost-password',
                 permission=NO_PERMISSION_REQUIRED,
                 renderer='/admin/lost-password.xhtml')
    def lost_password(self):
        """ Mechanism to recover lost-password."""
        form = UsernameForm(self.request.POST)
        captcha_form = CaptchaForm(self.request.POST)

        # Override username validator
        from wtforms import validators

        form.username.validators = [validators.Required()]

        if self.request.method == 'POST' \
                and ('form.save.person-infos' in self.request.params):
            if captcha_form.validate():
                if form.validate():
                    self.person = provider.get_people_by_username(
                        form.username.data)

                    if not self.person:
                        self.request.session.flash(
                            _('No such account exists'), 'error')
                        return dict(form=form)
                    elif self.person.status in [
                        AccountStatus.LOCKED,
                        AccountStatus.LOCKED_BY_ADMIN,
                        AccountStatus.DISABLED]:
                        self.request.session.flash(
                            _('This account is blocked'), 'error')
                        return redirect_to(self.request, 'home')

                    self.person.password_token = generate_token()
                    self.person.status = AccountStatus.PENDING.value

                    register.add_people(self.person)
                    register.save_account_activity(
                        self.request, self.person.id,
                        AccountLogType.ASKED_RESET_PASSWORD.value)

                    register.flush()

                    recipient = [self.person.email]
                    if self.person.recovery_email:
                        recipient.append(self.person.recovery_email)

                    self.notify(NotificationRequest(
                        request=self.request,
                        topic='user.password.reset',
                        people=self.person,
                        organisation=Config.get('project.organisation'),
                        reset_url=self.request.route_url(
                            'reset-password',
                            username=self.person.username,
                            token=self.person.password_token),
                        template='account_update',
                        target_email=recipient
                    ))
                    self.request.session.flash(
                        _('Check your email to finish the process'), 'info')
                    return redirect_to(
                        self.request, 'people-profile', id=self.person.id)

        return dict(form=form, captchaform=captcha_form)

    @view_config(route_name='reset-password',
                 permission=NO_PERMISSION_REQUIRED,
                 renderer='/admin/reset-password.xhtml')
    def reset_password(self):
        """ Mechanism to reset a lost-password."""
        try:
            username = self.request.matchdict['username']
            token = self.request.matchdict['token']
        except KeyError:
            return HTTPBadRequest('No username or token specified')

        self.person = provider.get_people_by_password_token(username, token)

        if not self.person:
            raise HTTPNotFound('No user found with this token')

        form = ResetPasswordPeopleForm(self.request.POST)

        if self.request.method == 'POST' \
                and ('form.save.person-infos' in self.request.params):
            if form.validate():
                register.update_password(form, self.person)
                self.person.status = AccountStatus.ACTIVE.value
                register.save_account_activity(
                    self.request, self.person.id,
                    AccountLogType.RESET_PASSWORD.value)
                register.flush()
                self.request.session.flash(_('Password reset'), 'info')
                return redirect_to(
                    self.request, 'people-profile', id=self.person.id)

        return dict(form=form, username=username, token=token)

    @view_config(route_name='people-password', permission='authenticated',
                 renderer='/people/edit-password.xhtml')
    def update_password(self):
        """" People password change."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest('No id specified')

        self.person = provider.get_people_by_id(self.id)

        if not self.person:
            raise HTTPNotFound(_(u'The person you are looking for'
                                 'do not exist.'))

        self.notify(PasswordChangeRequested(self.request, self.person))

        form = UpdatePasswordForm(self.request.POST, self.person)

        if self.request.method == 'POST' and form.validate():
            pv = PasswordValidator(self.person, form.old_password.data)

            if pv.is_valid \
                    and form.new_password.data == form.password.data:
                del form.old_password
                del form.new_password
                register.update_password(form, self.person)
                register.save_account_activity(
                    self.request,
                    self.person.id,
                    AccountLogType.UPDATE_PASSWORD.value)
                self.request.session.flash('Password updated', 'info')
                return redirect_to(self.request, 'people-profile', id=self.id)

        return dict(form=form, _id=self.id)

    @view_config(route_name='people-token', permission='authenticated',
                 renderer='/people/access-token.xhtml')
    def access_token(self):
        """ People's access token."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest('No id specified')

        form = AccountPermissionForm(self.request.POST)

        # Sets up allowed permissions from which a person could generate
        # a token with, based on its account's privileges.
        allowed_perms = [
            AccountPermissionType.CAN_READ_PUBLIC_INFO,
            AccountPermissionType.CAN_READ_PEOPLE_FULL_INFO,
            AccountPermissionType.CAN_READ_AND_EDIT_PEOPLE_INFO
        ]

        if self.request.authenticated_is_group_editor():
            allowed_perms.append(AccountPermissionType.CAN_EDIT_GROUP_INFO)
        elif self.request.authenticated_is_admin():
            allowed_perms.append(AccountPermissionType.CAN_EDIT_GROUP_MEMBERSHIP)
            allowed_perms.append(AccountPermissionType.CAN_READ_AND_EDIT_SETTINGS)

        form.perm.choices = [(p.value, p.name) for p in allowed_perms]

        if self.request.method == 'POST':

            if 'form.save.token' in self.request.params:
                if form.validate():
                    token = generate_token()
                    register.add_token(
                        form.desc.data,
                        token,
                        form.perm.data,
                        person_id=self.id)
                    register.save_account_activity(
                        self.request, self.id,
                        AccountLogType.REQUESTED_API_KEY.value)
                    self.request.session.flash(token, 'tokens')
                else:
                    log.error('Invalid token: %s', form.perm.data)

            if 'form.delete.token' in self.request.params:
                perm = int(self.request.params['form.delete.token'])
                register.remove_token(perm)
                # prevent from printing out deleted token in url
                return redirect_to(self.request, 'people-token', id=self.id)

        perms = provider.get_account_permissions_by_people_id(self.id)

        # Prevent client/user from requesting direct url
        # TODO: move this to Auth provider?
        if len(perms) > 0:
            self.person = perms[0].account
            if self.request.authenticated_userid != self.person.username:
                return redirect_to(self.request, 'people-profile', id=self.id)
        else:
            if self.person:
                if self.request.authenticated_userid != self.person.username:
                    return redirect_to(self.request, 'people-profile', id=self.id)
            else:
                self.person = provider.get_people_by_id(self.id)

        return dict(
            permissions=perms,
            person=self.person,
            # access=permission,
            pform=form)
