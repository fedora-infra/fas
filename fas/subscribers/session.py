# -*- coding: utf-8 -*-

from pyramid.events import (
    subscriber,
    NewRequest
)

from fas.utils import _, Config

# kept around for testing against checking below.
from pyramid.session import check_csrf_token
from pyramid.security import forget

from pyramid.httpexceptions import HTTPUnauthorized

# Disable for a short while testing sessions
# @subscriber(NewRequest)
# def login_validity(event):
    # """ Check login session validity on client's request. """
    # request = event.request
    # response = request.response
    # if not request.params.get('Cookie'):
        # headers = forget(request)
        # response.headerlist.extend(headers)


@subscriber(NewRequest)
def csrf_validity(event):
    """ Check CSRF token validity on client's requests. """
    request = event.request
    user = getattr(request, 'user', None)
    csrf = request.params.get('csrf_token')
    if (request.method == 'POST' or request.is_xhr) and (
        user and user.is_authenticated()) and (
            csrf != unicode(request.session.get_csrf_token())):
        raise HTTPUnauthorized


@subscriber(NewRequest)
def check_usersame(event):
    """ Check that authenticated user has valid username"""
    if event.request.authenticated_userid\
     in Config.get('blacklist.username').split(','):
        event.request.session.flash(
            _(u'Your username %s is forbidden! Please, update it'
            % event.request.authenticated_userid), 'error')

