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
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from fas.forms.account import AccountPermissionForm, TrustedPermissionForm

from fas.models import MembershipStatus
from fas.models import MembershipRole
import fas.models.provider as provider
import fas.models.register as register

from fas.forms.people import ContactInfosForm
from fas.forms.group import EditGroupForm, EditGroupTypeForm
from fas.forms.group import GroupListForm, GroupTypeListForm
from fas.forms.la import EditLicenseForm, SignLicenseForm, LicenseListForm
from fas.forms.certificates import EditCertificateForm
from fas.forms.certificates import CreateClientCertificateForm

from fas.events import GroupRemovalRequested, GroupCreated
from fas.events import GroupTypeRemovalRequested
from fas.events import LicenseRemovalRequested
from fas.security import generate_token

from fas.views import redirect_to
from fas.lib.captcha import Captcha
from fas.util import Config, setup_group_form
from fas.lib.fgithub import Github
from fas.lib.certificatemanager import CertificateManager

from fas.events import NewClientCertificateCreated

import logging

log = logging.getLogger(__name__)


class Admin(object):
    def __init__(self, request):
        self.request = request
        self.notify = self.request.registry.notify
        self.id = -1

    @view_config(route_name='settings', permission='admin',
                 renderer='/admin/panel.xhtml')
    def index(self):
        """ Admin panel page."""

        group_form = GroupListForm(self.request.POST)
        grouptype_form = GroupTypeListForm(self.request.POST)
        license_form = LicenseListForm(self.request.POST)
        token_form = AccountPermissionForm(self.request.POST)
        trustedperm_form = TrustedPermissionForm(self.request.POST)

        group_form.id.choices = [
            (group.id, group.name) for group in provider.get_groups()]

        grouptype_form.id.choices = [
            (gt.id, gt.name) for gt in provider.get_group_types()
        ]

        license_form.id.choices = [
            (la.id, la.name) for la in provider.get_licenses()
        ]

        trustedperm_form.id.choices = [
            (tp.id, tp.application) for tp in provider.get_trusted_perms()
        ]

        if self.request.method == 'POST':
            key = None
            if ('form.remove.group' in self.request.params) \
                    and group_form.validate():
                key = group_form.id.data
                self.notify(GroupRemovalRequested(self.request, key))
                register.remove_group(key)

            if ('form.remove.grouptype' in self.request.params) \
                    and grouptype_form.validate():
                key = grouptype_form.id.data
                self.notify(GroupTypeRemovalRequested(self.request, key))
                register.remove_grouptype(key)

            if ('form.remove.license' in self.request.params) \
                    and license_form.validate():
                key = license_form.id.data
                self.notify(LicenseRemovalRequested(self.request, key))
                register.remove_license(key)
            if ('form.generate.key' in self.request.params) \
                    and token_form.validate():
                token = generate_token()
                secret = generate_token(128)
                register.add_token(
                    description=token_form.desc.data,
                    permission=token_form.perm.data,
                    token=token,
                    trusted=True,
                    secret=secret)
                self.request.session.flash(token, 'tokens')
                self.request.session.flash(secret, 'secret')

            # self.notify()

        return dict(groupform=group_form,
                    gtypeform=grouptype_form,
                    licenseform=license_form,
                    trustedpermform=trustedperm_form,
                    tpermform=token_form)

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

        form = setup_group_form(self.request)

        if self.request.method == 'POST' \
                and ('form.save.group-details' in self.request.params):
            if form.validate():
                group = register.add_group(form)
                self.notify(GroupCreated(self.request, group))
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

        if self.request.method == 'POST' \
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

        if self.request.method == 'POST' \
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

        if self.request.method == 'POST' \
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

        if self.request.method == 'POST' \
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

        if self.request.method == 'POST' \
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

    @view_config(route_name='add-certificate', permission='admin',
                 renderer='/admin/edit-certificate.xhtml')
    def add_certificate(self):
        """ Add new certificates form page. """
        form = EditCertificateForm(self.request.POST)

        if self.request.method == 'POST' \
                and ('form.save.certificate' in self.request.params):
            if form.validate():
                register.add_certificate(form)
                return redirect_to('/settings')

        return dict(form=form)

    @view_config(route_name='get-client-cert', permission='authenticated')
    def get_client_cert(self):
        """ Generate and return as attachment client certificate. """
        response = self.request.response
        person = self.request.get_user
        form = CreateClientCertificateForm(self.request.POST)

        if self.request.method == 'POST' \
                and ('form.create.client_cert' in self.request.params):
            if not form.validate():
                # Should redirect to previous url
                log.error('Invalid form value from requester :'
                          'cacert: %s, group_id: %s, group_name: %s' %
                          (form.cacert.data, form.group_id.data, form.group_name.data))
                raise redirect_to('/')
            else:
                # Setup headers
                headers = response.headers
                headers['Accept'] = 'text'
                headers['Content-Description'] = 'Files transfer'
                headers['Content-Type'] = 'text'
                headers['Accept-Ranges'] = 'bytes'
                headers['Content-Disposition'] = \
                    'attachment; filename=%s-%s.cert' \
                    % (Config.get('project.name'), str(form.group_name.data))

                client_cert = provider.get_client_certificate(
                    form.cacert.data, person)

                serial = 1

                if client_cert:
                    log.debug('Found client certificate')
                    cacert = client_cert.cacert
                    if not Config.get('project.group.cert.always_renew'):
                        response.body = client_cert.certificate
                        return response
                    else:
                        serial = client_cert.serial + 1
                else:
                    cacert = provider.get_certificate(form.cacert.data)

                certm = CertificateManager(cacert.cert, cacert.cert_key, Config)

                (new_cert, new_key) = certm.create_client_certificate(
                    person.username,
                    person.email,
                    form.client_cert_desc.data,
                    serial)

                cert = new_cert
                cert += new_key

                log.debug('Registering client certificate: %s', cert)

                register.add_client_certificate(cacert, person, cert, serial)
                self.notify(NewClientCertificateCreated(
                    self.request, person, form.group_name.data))

                response.body = cert

                return response

        raise redirect_to('/')

