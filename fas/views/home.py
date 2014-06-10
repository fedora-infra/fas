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

from fas.utils import get_config
import fas.models.provider as provider


@view_defaults(renderer='/home.xhtml')
class Home:

    def __init__(self, request):
        self.request = request
        self.logged_in = self.request.authenticated_userid
        self.config = get_config

    @view_config(route_name='home')
    def index(self):
        """ Main page. """
        return {'one': 'admin',
            'project': 'fas',
            'project_name': self.config('project.name')}

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
        came_from = self.request.params.get('came_from', referrer)

        if 'form.submitted' in self.request.params:
            login = self.request.params['login']
            password = self.request.params['password']
            person = provider.get_people_by_username(login)
            if person:
                #TODO: this is for testing only. will be part of validator.
                if person.password == password:
                    headers = remember(self.request, login)
                    self.request.session.get_csrf_token()
                    return HTTPFound(location=came_from, headers=headers)
            message = 'Login failed. Invalid username or password!'
            self.request.session.flash('info message')
            self.request.session.pop_flash()

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
        came_from = self.request.params.get('came_from', self.request.url)

        return HTTPFound(location=came_from, headers=headers)