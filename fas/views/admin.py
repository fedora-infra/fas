# -*- coding: utf-8 -*-

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED

from fas.models import MembershipStatus
from fas.models import MembershipRole
import fas.models.provider as provider
import fas.models.register as register

from fas.forms.people import ContactInfosForm
from fas.forms.group import EditGroupForm, EditGroupTypeForm
from fas.forms.la import EditLicenseForm, SignLicenseForm

from fas.views import redirect_to
from fas.utils.captcha import Captcha
from fas.utils import Config
from fas.utils.fgithub import Github


class Admin(object):

    def __init__(self, request):
        self.request = request
        self.id = -1

    @view_config(route_name='settings', permission='admin')
    def index(self):
        """ Admin panel page."""
        return Response('This is an empty page')

    @view_config(route_name='captcha-image', renderer='jpeg')
    def captcha_image(self):
        try:
            cipherkey = self.request.matchdict['cipherkey']
        except KeyError:
            return HTTPBadRequest

        captcha = Captcha()

        return captcha.get_image(cipherkey)

    @view_config(route_name='add-group', permission='group_edit',
                 renderer='/groups/edit.xhtml')
    def add_group(self):
        """ Group addition page."""

        form = EditGroupForm(self.request.POST)

        form.parent_group_id.choices = [
            (group.id, group.name) for group in provider.get_groups()]
        form.parent_group_id.choices.insert(0, (-1, u'-- None --'))

        form.group_type.choices = [
            (t.id, t.name) for t in provider.get_group_types()]
        form.group_type.choices.insert(0, (-1, u'-- Select a group type --'))

        form.license_sign_up.choices.insert(0, (-1, u'-- None --'))

        if self.request.method == 'POST'\
                and ('form.save.group-details' in self.request.params):
            if form.validate():
                group = register.add_group(form)
                register.add_membership(
                    group.id, group.owner_id,
                    MembershipStatus.APPROVED,
                    MembershipRole.ADMINISTRATOR)
                if form.bound_to_github.data:
                    g = Github()
                    g.create_group(
                        name=group.name,
                        repo=group.name,
                        access='push'
                    )
                return redirect_to('/group/details/%s' % group.id)

        return dict(form=form)

    @view_config(route_name='remove-group', permission='admin')
    def remove_group(self):
        """ Remove a group from system."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        # TODO: Add a confirmation form if group has members and child groups.
        group = provider.get_group_by_id(self.id)

        register.remove_group(group.id)
        return redirect_to('/groups')

        return dict()  # This should redirect to came_from

    @view_config(route_name='add-license', permission='admin',
                 renderer='/admin/edit-license.xhtml')
    def add_license(self):
        """ Add license page."""
        form = EditLicenseForm(self.request.POST)

        if self.request.method == 'POST'\
                and ('form.save.license' in self.request.params):
            if form.validate():
                la = register.add_license(form)
                # return redirect_to('/settings/option#licenses%s' % la.id)
                # Redirect to home as admin page not view-able now
                return redirect_to('/')

        return dict(form=form)

    @view_config(route_name='edit-license', permission='admin',
                 renderer='/admin/edit-license.xhtml')
    def edit_license(self):
        """ Edit license infos form page."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        la = provider.get_license_by_id(self.id)

        form = EditLicenseForm(self.request.POST, la)

        if self.request.method == 'POST'\
                and ('form.save.license' in self.request.params):
            if form.validate():
                form.populate_obj(la)
                # Redirect to home as admin page not view-able now
                return redirect_to('/')

        return dict(form=form)

    @view_config(route_name='remove-license', permission='admin')
    def remove_license(self):
        """ Remove a license from system. """
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        register.remove_license(self.id)

        # Redirect to home as admin page not view-able now
        return redirect_to('/')

        return dict()

    @view_config(route_name='sign-license', permission='authenticated')
    def sign_license(self):
        """ Sign license from given people """
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        person = self.request.get_user
        userform = ContactInfosForm(self.request.POST, person)
        form = SignLicenseForm(self.request.POST)

        userform.username.data = person.username
        userform.fullname.data = person.fullname
        userform.email.data = person.email

        if self.request.method == 'POST'\
        and ('form.sign.license' in self.request.params):
            if userform.validate() and form.validate():
                userform.populate_obj(person)

                form.people.data = person.id
                form.license.data = self.id
                register.add_signed_license(form)

                return redirect_to(self.request.params['form.sign.license'])

        return redirect_to('/')

    @view_config(route_name='add-grouptype', permission='admin',
                 renderer='/admin/edit-grouptype.xhtml')
    def add_grouptype(self):
        """ Add/Edit group type's page."""
        form = EditGroupTypeForm(self.request.POST)

        if self.request.method == 'POST'\
                and ('form.save.grouptype' in self.request.params):
            if form.validate():
                gt = register.add_grouptype(form)
                # return redirect_to('/settings/option#GroupsType%s' % la.id)
                # Redirect to home as admin page not view-able now
                return redirect_to('/')

        return dict(form=form)

    @view_config(route_name='edit-grouptype', permission='admin',
                 renderer='/admin/edit-grouptype.xhtml')
    def edit_grouptype(self):
        """ Edit group type' infos form page."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        gt = provider.get_grouptype_by_id(self.id)

        form = EditLicenseForm(self.request.POST, gt)

        if self.request.method == 'POST'\
                and ('form.save.grouptype' in self.request.params):
            if form.validate():
                form.populate_obj(gt)
                # Redirect to home as admin page not view-able now
                return redirect_to('/')

        return dict(form=form)

    @view_config(route_name='remove-grouptype', permission='admin')
    def remove_grouptype(self):
        """ Remove group type page."""
        return dict()
