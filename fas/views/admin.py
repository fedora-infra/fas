# -*- coding: utf-8 -*-

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED

import fas.models.provider as provider
import fas.models.register as register

from fas.forms.group import EditGroupForm
from fas.forms.la import EditLicenseForm

from fas.views import redirect_to
from fas.utils import Config


class Admin(object):

    def __init__(self, request):
        self.request = request
        self.id = -1

    @view_config(route_name='settings', permission='admin')
    def index(self):
        """ Admin panel page."""
        return Response('This is an empty page')

    @view_config(route_name='add-group', permission='group_edit',
        renderer='/groups/edit.xhtml')
    def add_group(self):
        """ Group addition page."""

        form = EditGroupForm(self.request.POST)

        if self.request.method == 'POST'\
         and ('form.save.group-details' in self.request.params):
            if form.validate():
                group = register.add_group(form)
                register.add_membership(group, group.owner_id, 5)
                return redirect_to('/group/details/%s' % group.id)

        return dict(form=form)

    @view_config(route_name='remove-group', permission='admin')
    def remove_group(self):
        """ Remove a group from system."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        #TODO: Add a confirmation form if group has members and child groups.
        group = provider.get_group_by_id(self.id)

        register.remove_group(group.id)
        return redirect_to('/groups')

        return dict()  #This should redirect to came_from

    @view_config(route_name='add-license', permission='admin',
        renderer='/admin/edit-license.xhtml')
    def add_license(self):
        """ Add license page."""
        form = EditLicenseForm(self.request.POST)

        if self.request.method == 'POST'\
         and ('form.save.license' in self.request.params):
            if form.validate():
                la = register.add_license(form)
                #return redirect_to('/settings/option#licenses%s' % la.id)
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

