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

from pyramid.httpexceptions import (
    HTTPFound,
)
from pyramid.view import (
    view_config,
    view_defaults,
    forbidden_view_config,
)
from pyramid.security import (
    remember,
    forget,
)

from fas.util import Config
from fas.security import LoginStatus, process_login
import fas.models.provider as provider
from fas.util import _


@view_defaults(renderer='/home.xhtml')
class Home:
    def __init__(self, request):
        self.request = request
        self.logged_in = self.request.authenticated_userid
        self.notify = self.request.registry.notify
        self.config = Config.get

    @view_config(route_name='home')
    def index(self):
        """ Main page. """
        return {
            'one': 'admin',
            'project': 'fas',
            'project_name': self.config('project.name')
        }

    @view_config(route_name='login', renderer='/login.xhtml')
    @forbidden_view_config(renderer='/login.xhtml')
    def login(self):
        """ Logs user in. """
        message = ''
        login = ''
        password = ''

        login_url = self.request.route_url('login')
        referrer = self.request.url
        if referrer == login_url:
            referrer = '/'  # never use the login form itself as came_from
        came_from = self.request.params.get('redirect', referrer)

        if 'form.submitted' in self.request.params:
            login = self.request.params['login']
            password = self.request.params['password']
            person = provider.get_people_by_username(login)

            result = process_login(self.request, person, password)
            # self.notify(LoginRequested(self.request, person))

            if result == LoginStatus.SUCCEED:
                headers = remember(self.request, login)
                return HTTPFound(location=came_from, headers=headers)
            elif result == LoginStatus.FAILED_INACTIVE_ACCOUNT:
                self.request.session.flash(
                    _('Login failed, this account has not been activated,'
                      'please go check your emails and follow the'
                      'the procedure to activate your account'),
                    'login')
            elif result == LoginStatus.FAILED_LOCKED_ACCOUNT:
                self.request.session.flash(
                    _('Login blocked.'), 'login')
            else:
                self.request.session.flash(
                    _('Invalid login or password'), 'login')

        return dict(
            message=message,
            url=self.request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
        )

    @view_config(route_name='logout')
    def logout(self):
        """ Logs authenticated user out. """
        headers = forget(self.request)
        came_from = self.request.params.get('redirect', self.request.url)

        return HTTPFound(location=came_from, headers=headers)
