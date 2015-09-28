# -*- coding: utf-8 -*-
#
# Copyright © 2015 Xavier Lamien.
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
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPBadRequest

from pyramid.security import NO_PERMISSION_REQUIRED

from fas.models import AccountStatus

from fas.models.people import People
from fas.models import provider
from fas.models import register

from fas.forms.people import NewPeopleForm
from fas.forms.people import EditPeopleForm
from fas.forms.captcha import CaptchaForm
from fas.forms.la import SignLicenseForm

from fas.views import redirect_to

from fas.security import generate_token

from fas.events import NewUserRegistered

from fas.lib.passwordmanager import PasswordManager
from fas.util import _

import logging

log = logging.getLogger(__name__)


class Register(object):
    def __init__(self, request):
        self.request = request
        self.id = -1
        self.person = None
        self.notify = self.request.registry.notify

    @view_config(route_name='people-new', permission=NO_PERMISSION_REQUIRED,
                 renderer='/register.xhtml')
    def account(self):
        """ Create a user account."""
        if self.request.authenticated_userid:
            return redirect_to(
                '/people/profile/%s' % self.request.authenticated_userid)

        licenses = provider.get_licenses()

        form = NewPeopleForm(self.request.POST)
        captchaform = CaptchaForm(self.request.POST)
        peopleform = EditPeopleForm(self.request.POST)

        la = None
        la_form = None

        if licenses:
            for la in licenses:
                if la.enabled_at_signup:
                    la = la
                    la_form = SignLicenseForm(self.request.POST)
                    # NB: should we allow multiple licenses at signup?
                    break

        if self.request.method == 'POST' \
                and ('form.register' in self.request.params):
            self.person = People()
            if not captchaform.validate() and not la_form.validate():
                log.debug('captcha and license agreement are not valid')
            else:
                if form.validate():

                    self.person.username = form.username.data
                    self.person.email = form.email.data
                    self.person.fullname = form.fullname.data

                    pwdman = PasswordManager()
                    self.person.password = pwdman.generate_password(
                        form.password.data)
                    self.person.password_token = generate_token()

                    # Disabled validation while testing optional infos
                    # if peopleform.validate():
                    self.person.avatar = peopleform.avatar.data
                    self.person.introduction = peopleform.introduction.data
                    self.person.ircnick = peopleform.ircnick.data
                    self.person.postal_address = peopleform.postal_address.data
                    self.person.telephone = peopleform.telephone.data

                    register.add_people(self.person)
                    register.flush()

                    if la_form:
                        la_form.license.data = la.id
                        la_form.people.data = self.person.id
                        register.add_signed_license(la_form)

                    self.request.registry.notify(
                        NewUserRegistered(self.request, self.person)
                    )

                    self.request.session.flash(
                        _('Account created, please check your email to finish '
                          'the process'), 'info')
                    return redirect_to('/people/profile/%s' % self.person.id)

        return dict(form=form, captchaform=captchaform, licensesform=[la_form],
                    peopleform=peopleform, licenses=licenses)

    @view_config(
        route_name='people-confirm-account',
        permission=NO_PERMISSION_REQUIRED)
    def confirm_account(self):
        """ Confirm a user account creation."""
        try:
            username = self.request.matchdict['username']
            token = self.request.matchdict['token']
        except KeyError:
            return HTTPBadRequest()

        self.person = provider.get_people_by_password_token(username, token)

        if not self.person:
            raise HTTPNotFound('No user found with this token')

        self.person.password_token = None
        self.person.status = AccountStatus.ACTIVE
        register.add_people(self.person)
        self.request.session.flash(_('Account activated'), 'info')

        return redirect_to('/people/profile/%s' % self.person.id)
