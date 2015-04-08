# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED

import fas.models.provider as provider
import fas.models.register as register

from fas.security import generate_token

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

from fas.security import PasswordValidator
from fas.views import redirect_to
from fas.utils import compute_list_pages_from
from fas.utils.avatar import gen_libravatar

from fas.models import (
    AccountPermissionType as permission,
    AccountStatus,
    AccountLogType,
    MembershipStatus
    )

from fas.events import PasswordChangeRequested

from fas.notifications.email import Email

# temp import, i'm gonna move that away
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

import GeoIP
import logging
from fas.utils import _, Config
from socket import error as socket_error

log = logging.getLogger(__name__)


class People(object):

    def __init__(self, request):
        self.request = request
        self.id = -1
        self.person = None
        self.notify = self.request.registry.notify

    def redirect_to_profile(self):
        return redirect_to('/people/profile/%s' % self.id)

    @view_config(route_name='people', renderer='/people/list.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    @view_config(route_name='people-paging', renderer='/people/list.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    def paging(self):
        """ People list's view with paging. """
        try:
            page = int(self.request.matchdict.get('pagenb', 1))
        except ValueError:
            return HTTPBadRequest()

        # TODO: get limit from config file or let user choose in between
        #      predefined one ?
        people = provider.get_people(50, page)
        peoples = provider.get_people(count=True)

        pages = compute_list_pages_from(peoples, 50)

        if page > pages:
            return HTTPBadRequest()

        return dict(
            people=people,
            count=int(peoples),
            page=page,
            pages=pages
            )

    @view_config(
        route_name='people-search-rd', renderer='/people/search.xhtml')
    def search_redirect(self):
        """ Redirect the search to the proper url. """
        _id = self.request.params.get('q', '*')
        return redirect_to('/people/search/%s' % _id)

    @view_config(
        route_name='people-search', renderer='/people/search.xhtml')
    @view_config(
        route_name='people-search-paging', renderer='/people/search.xhtml')
    def search(self):
        """ Search people page. """
        try:
            _id = self.request.matchdict['pattern']
        except KeyError:
            return HTTPBadRequest()
        page = int(self.request.matchdict.get('pagenb', 1))

        username = None
        try:
            _id = int(_id)
        except:
            username = _id

        if username:
            if '*' in username:
                username = username.replace('*', '%')
            else:
                username = username + '%'
            people = provider.get_people(50, page, pattern=username)
            peoples = provider.get_people(pattern=username, count=True)
        else:
            people = provider.get_people_by_id(_id)
            peoples = 1

        if not people:
            self.request.session.flash(
                _('No user found for the query: %s' % _id), 'error')
            return redirect_to('/people')

        pages = compute_list_pages_from(peoples, 50)

        if page > pages:
            return HTTPBadRequest()

        if username and len(people) == 1 and page == 1:
            self.request.session.flash(
                _("Only one user matching, redirecting to the user's page"),
                'info')
            return redirect_to('/people/profile/%s' % people[0].id)

        return dict(
            people=people,
            page=page,
            pages=pages,
            count=int(peoples),
            pattern=_id
        )

    @view_config(route_name='people-profile', renderer='/people/profile.xhtml')
    def profile(self):
        """ People profile page. """
        try:
            _id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        username = None
        try:
            _id = int(_id)
        except:
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
                return redirect_to('/people')

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

        return dict(
            person=self.person,
            form=form,
            formavatar=form_avatar,
            formsshkey=form_sshkey,
            form_gpgfp=form_gpgfp,
            membership=membership
        )

    @view_config(route_name='people-activities',
                 renderer='/people/activities.xhtml')
    def activities(self):
        """ People's activities page. """
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        activities = provider.get_account_activities_by_people_id(self.id)

        # Prevent client/user from requesting direct url
        if len(activities) > 0:
            self.person = activities[0].person
            if self.request.authenticated_userid != self.person.username:
                return self.redirect_to_profile()
        else:
            if self.request.authenticated_userid != self.person.username\
                    or self.request.authenticated_userid == \
                    self.person.username:
                return self.redirect_to_profile()

        return dict(activities=activities, person=self.person)

    @view_config(route_name='people-edit', permission='authenticated',
                 renderer='/people/edit-infos.xhtml')
    def edit_infos(self):
        """ Profile's edit page."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

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
            return redirect_to('/people/profile/%s' % self.id)

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
            (l, l) for l in list(Config.get('locale.available').split(','))]

        if self.request.method == 'POST'\
                and ('form.save.person-infos' in self.request.params):
            if form.validate():
                form.populate_obj(self.person)
                return redirect_to('/people/profile/%s' % self.id)

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

        email = Email('account_update')

        if self.request.method == 'POST'\
                and ('form.save.person-infos' in self.request.params):
            if captcha_form.validate():
                if form.validate():
                    self.person = provider.get_people_by_username(
                        form.username.data)

                    if not self.person:
                        self.request.session.flash(
                            _('No such account exists'), 'error')
                        return dict(form=form, captchaform=captcha_form)
                    elif self.person.status in [
                            AccountStatus.LOCKED,
                            AccountStatus.LOCKED_BY_ADMIN,
                            AccountStatus.DISABLED]:
                        self.request.session.flash(
                            _('This account is blocked'), 'error')
                        return redirect_to('/')

                    self.person.password_token = generate_token()
                    self.person.status = AccountStatus.PENDING

                    register.add_people(self.person)
                    register.save_account_activity(
                        self.request, self.person.id,
                        AccountLogType.ASKED_RESET_PASSWORD)

                    register.flush()

                    email.set_msg(
                        topic='password-reset',
                        people=self.person,
                        organisation=Config.get('project.organisation'),
                        reset_url=self.request.route_url(
                            'reset-password',
                            username=self.person.username,
                            token=self.person.password_token))
                    rcpt = [self.person.email]
                    if self.person.recovery_email:
                        rcpt.append(self.person.recovery_email)
                    try:
                        email.send(rcpt)
                    except socket_error as err:
                        self.request.session.flash(
                            _("We're having trouble sending your recovery " +
                              "email. Please contact us for assistance!"), 'error')
                        return dict(form=form, captchaform=captcha_form)
                    self.request.session.flash(
                        _('Check your email to finish the process'), 'info')
                    return redirect_to('/people/profile/%s' % self.person.id)

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
            return HTTPBadRequest()

        self.person = provider.get_people_by_password_token(username, token)

        if not self.person:
            raise HTTPNotFound('No user found with this token')

        form = ResetPasswordPeopleForm(self.request.POST)

        if self.request.method == 'POST'\
                and ('form.save.person-infos' in self.request.params):
            if form.validate():
                register.update_password(form, self.person)
                self.person.status = AccountStatus.ACTIVE
                register.save_account_activity(
                    self.request, self.person.id,
                    AccountLogType.RESET_PASSWORD)
                register.flush()
                self.request.session.flash(_('Password reset'), 'info')
                return redirect_to('/people/profile/%s' % self.person.id)

        return dict(form=form, username=username, token=token)

    @view_config(route_name='people-password', permission='authenticated',
                 renderer='/people/edit-password.xhtml')
    def update_password(self):
        """" People password change."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

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
                    self.person.id, AccountLogType.UPDATE_PASSWORD)
                self.request.session.flash('Password updated', 'info')
                return redirect_to('/people/profile/%s' % self.id)

        return dict(form=form, _id=self.id)

    @view_config(route_name='people-token', permission='authenticated',
                 renderer='/people/access-token.xhtml')
    def access_token(self):
        """ People's access token."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        form = AccountPermissionForm(self.request.POST)

        if self.request.method == 'POST':

            if 'form.save.token' in self.request.params:
                if form.validate():
                    token = generate_token()
                    register.add_token(
                        form.desc.data,
                        token,
                        form.perm.data,
                        people_id=self.id)
                    register.save_account_activity(
                                self.request, self.id,
                                AccountLogType.REQUESTED_API_KEY)
                    self.request.session.flash(token, 'tokens')
                else:
                    log.error('Invalid token: %s', form.perm.data)

            if 'form.delete.token' in self.request.params:
                perm = int(self.request.params['form.delete.token'])
                register.remove_token(perm)
                # prevent from printing out deleted token in url
                return HTTPFound(
                    self.request.route_path('people-token', id=self.id))

        perms = provider.get_account_permissions_by_people_id(self.id)

        # Prevent client/user from requesting direct url
        # TODO: move this to Auth provider?
        if len(perms) > 0:
            self.person = perms[0].account
            if self.request.authenticated_userid != self.person.username:
                return self.redirect_to_profile()
        else:
            if self.person:
                if self.request.authenticated_userid != self.person.username:
                    return self.redirect_to_profile()
            else:
                self.person = provider.get_people_by_id(self.id)

        return dict(
            permissions=perms,
            person=self.person,
            access=permission,
            pform=form)

