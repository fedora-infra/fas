# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED

import fas.models.provider as provider
import fas.models.register as register

from fas.security import generate_token

from fas.forms.people import EditPeopleForm
from fas.forms.people import NewPeopleForm
from fas.forms.people import UpdateStatusForm
from fas.forms.people import UpdatePasswordForm

from fas.security import PasswordValidator
from fas.views import redirect_to
from fas.utils import compute_list_pages_from, generate_token
from fas.utils.notify import notify_account_creation
from fas.models import AccountPermissionType as permission
from fas.models.people import People as mPeople

# temp import, i'm gonna move that away
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from fas.utils import _


class People(object):

    def __init__(self, request):
        self.request = request
        self.id = -1
        self.person = None

    def redirect_to_profile(self):
        return redirect_to('/people/profile/%s' % self.id)

    @view_config(route_name='people')
    def index(self):
        """ People list landing page. """
        return redirect_to('/people/page/1')

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

        pages, count = compute_list_pages_from('people', 50)

        if page > pages:
            return HTTPBadRequest()

        return dict(
            people=people,
            count=count,
            page=page,
            pages=pages
            )

    @view_config(route_name='people-profile', renderer='/people/profile.xhtml')
    def profile(self):
        """ People profile page. """
        try:
            _id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        self.person = provider.get_people_by_id(_id)
        if not self.person:
            raise HTTPNotFound('No such user found')

        form = UpdateStatusForm(self.request.POST, self.person)
        if self.request.method == 'POST' and form.validate():
            form.populate_obj(self.person)

        return dict(
            person=self.person,
            form=form,
            membership=self.person.group_membership
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

        self.person = provider.get_people_by_id(self.id)

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

        if self.request.method == 'POST'\
                and ('form.save.person-infos' in self.request.params):
            if form.validate():
                form.populate_obj(self.person)
                return redirect_to('/people/profile/%s' % self.id)

        return dict(form=form, id=self.id)

    @view_config(route_name='people-new', permission=NO_PERMISSION_REQUIRED,
                 renderer='/people/new.xhtml')
    def new_user(self):
        """ Create a user account."""
        form = NewPeopleForm(self.request.POST)

        if self.request.method == 'POST'\
                and ('form.save.person-infos' in self.request.params):
            self.person = mPeople()
            if form.validate():
                form.populate_obj(self.person)
                self.person.password_token = generate_token()
                register.add_people(self.person)
                register.flush()
                notify_account_creation(self.person)
                return redirect_to('/people/profile/%s' % self.person.id)

        return dict(form=form)

    @view_config(route_name='people-password', permission='authenticated',
                 renderer='/people/edit-password.xhtml')
    def update_password(self):
        """" People password change."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        self.person = provider.get_people_by_id(self.id)

        form = UpdatePasswordForm(self.request.POST, self.person)

        if self.request.method == 'POST' and form.validate():
            pv = PasswordValidator(self.person, form.old_password.data)

            if pv.is_valid() \
                    and form.new_password.data == form.password.data:
                del form.old_password
                del form.new_password
                register.update_password(form, self.person)
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

        if 'form.save.token' in self.request.params:
            perm = self.request.params['permission']
            desc = self.request.params['description']

            token = generate_token()
            register.add_token(self.id, desc, token, perm)
            self.request.session.flash(token, 'tokens')

        if 'form.delete.token' in self.request.params:
            perm = self.request.params['form.delete.token']
            register.remove_token(perm)
            # prevent from printing out deleted token in url
            return HTTPFound(
                self.request.route_path('people-token', id=self.id))

        perms = provider.get_account_permissions_by_people_id(self.id)

        token_perm = []
        token_perm.append(
            (permission.CAN_READ_PEOPLE_PUBLIC_INFO,
             _('client can read fas public\'s information')))
        token_perm.append(
            (permission.CAN_READ_PEOPLE_PUBLIC_INFO,
             _('client can read only you public account\'s information')))
        token_perm.append(
            (int(permission.CAN_READ_PEOPLE_FULL_INFO),
             _('client can read your full account information')))
        token_perm.append(
            (permission.CAN_READ_AND_EDIT_PEOPLE_INFO,
             _('client can read and edit your account\' information')))
        token_perm.append(
            (permission.CAN_EDIT_GROUP_INFO,
             _('client can edit fas group\'s information')))

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

        return dict(permissions=perms, person=self.person, access=token_perm)
