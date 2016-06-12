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

from pyramid.events import (
    subscriber,
    NewRequest
)

from fas.util import _, Config

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
    if (request.method == 'POST' or (
            request.method != 'GET' and request.is_xhr)) and (
            request.get_user) and (
                csrf != unicode(request.session.get_csrf_token())):
        raise HTTPUnauthorized


@subscriber(NewRequest)
def check_usersame(event):
    """ Check that authenticated user has valid username"""
    if event.request.authenticated_userid \
            in Config.get('blacklist.username').split(','):
        event.request.session.flash(
            _(u'Your username %s is forbidden! Please, update it'
              % event.request.authenticated_userid), 'error')
