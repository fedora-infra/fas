# -*- coding: utf-8 -*-

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
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

from fas.utils import Config
from fas.security import PasswordValidator
from fas.models import AccountStatus

import fas.models.provider as provider
import fas.models.register as register


@view_defaults(renderer='/home.xhtml')
class Home:

    def __init__(self, request):
        self.request = request
        self.logged_in = self.request.authenticated_userid
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

            blocked = True
            if person.status in [
                    AccountStatus.ACTIVE, AccountStatus.INACTIVE,
                    AccountStatus.ON_VACATION]:
                blocked = False

            pv = PasswordValidator(person, password)
            if pv.is_valid() and not blocked:
                headers = remember(self.request, login)
                self.request.session.get_csrf_token()
                register.save_account_activity(
                    self.request, person.id, AccountLogType.LOGGED_IN)
                return HTTPFound(location=came_from, headers=headers)

            if person.status == AccountStatus.PENDING:
                self.request.session.flash(
                    'Login failed, this account has not been activated, '
                    'please check your emails.', 'login')
            elif person.status in [
                    AccountStatus.LOCKED, AccountStatus.LOCKED_BY_ADMIN,
                    AccountStatus.DISABLED
                ]:
                self.request.session.flash(
                    'Login blocked.', 'login')
            else:
                self.request.session.flash('Login failed', 'login')

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
