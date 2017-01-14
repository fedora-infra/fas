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

from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.events import BeforeRender

from sqlalchemy import engine_from_config

from .release import get_release_info

import logging

log = logging.getLogger(__name__)

from .security import (
    groupfinder,
    authenticated_is_admin,
    authenticated_is_modo,
    authenticated_is_group_admin,
    authenticated_is_group_editor,
    authenticated_is_group_sponsor,
    penging_membership_requests,
    join_group,
    request_membership,
    requested_membership,
    remove_membership,
    ParamsValidator, TokenValidator)

from .models.provider import get_authenticated_user

from models import (
    DBSession,
    Base,
)

from .util import locale_negotiator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    from pyramid.session import SignedCookieSessionFactory
    session_factory = SignedCookieSessionFactory(
        settings['session.secret'],
        cookie_name='fas_session',
        timeout=int(settings['session.timeout']),
        max_age=int(settings['session.max_age']),
        reissue_time=int(settings['session.renew_time'])
    )

    config = Configurator(
        session_factory=session_factory,
        settings=settings,
        root_factory='fas.security.Root'
    )

    def add_renderer_globals(event):
       event['theme_static'] = settings['project.theme.path']

    from fas.renderers import jpeg
    config.add_renderer('jpeg', jpeg)

    config.include('pyramid_mako')

    config.add_mako_renderer('.xhtml', settings_prefix='mako.')

    config.add_static_view(
        name='static',
        path=settings['project.theme.path'],
        cache_max_age=int(settings['cache.max_age'])
    )

    authn_policy = AuthTktAuthenticationPolicy(
        settings['session.auth.secret'],
        cookie_name='fas_auth',
        hashalg=settings['session.auth.digest'],
        callback=groupfinder,
        timeout=int(settings['session.auth.timeout']),
        debug=log.isEnabledFor(logging.DEBUG)
    )

    authz_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.add_translation_dirs('fas:locale/')
    config.set_locale_negotiator(locale_negotiator)

    config.add_request_method(get_release_info, 'release', reify=True)
    config.add_request_method(get_authenticated_user, 'get_user', reify=True)
    config.add_request_method(
        authenticated_is_admin, 'authenticated_is_admin', reify=False)
    config.add_request_method(
        authenticated_is_modo, 'authenticated_is_modo', reify=False)
    config.add_request_method(
        authenticated_is_group_admin,
        'authenticated_is_group_admin',
        reify=False
    )
    config.add_request_method(
        authenticated_is_group_editor,
        'authenticated_is_group_editor',
        reify=False
    )
    config.add_request_method(
        authenticated_is_group_sponsor,
        'authenticated_is_group_sponsor',
        reify=False
    )
    config.add_request_method(
        join_group,
        'join_group',
        reify=False
    )
    config.add_request_method(
        request_membership,
        'request_membership',
        reify=False
    )
    config.add_request_method(
        requested_membership,
        'requested_membership',
        reify=False
    )
    config.add_request_method(
        remove_membership,
        'revoke_membership',
        reify=False
    )
    config.add_request_method(
        penging_membership_requests,
        'get_pending_ms_requests',
        reify=True
    )
    config.add_request_method(
        ParamsValidator,
        'param_validator',
        reify=True
    )
    config.add_request_method(
        TokenValidator,
        'token_validator',
        reify=True
    )

    # Test route
    config.add_route('test', '/test')

    # home pages
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    # People pages
    config.add_route('people', '/people')
    config.add_route('people-search-rd', '/people/search')
    config.add_route('people-search', '/people/search/{pattern}')
    config.add_route('people-search-paging', '/people/search/{pattern}/{pagenb}')
    config.add_route('people-new', '/register')
    config.add_route('people-confirm-account',
                     '/register/confirm/{username}/{token}')
    config.add_route('people-paging', '/people/page/{pagenb}')
    config.add_route('people-profile', '/people/profile/{id}')
    config.add_route('people-activities', '/people/profile/{id}/activities')
    config.add_route('people-token', '/people/profile/{id}/accesstoken')
    config.add_route('people-edit', '/people/profile/{id}/edit')
    config.add_route('people-password', '/people/profile/{id}/edit/password')

    # Groups pages
    config.add_route('groups', '/groups')
    config.add_route('groups-paging', '/groups/page/{pagenb}')
    config.add_route('group-details', '/group/details/{id}')
    config.add_route('group-edit', '/group/details/{id}/edit')
    config.add_route('group-search-rd', '/group/search')
    config.add_route('group-search', '/group/search/{pattern}')
    config.add_route('group-search-paging', '/group/search/{pattern}/{pagenb}')
    config.add_route('group-apply', '/group/apply/{id}')
    config.add_route('group-action', '/group/update/')
    config.add_route('group-pending-request', '/groups/pending-requests')

    # API requests
    config.add_route('api', '/api')
    config.add_route('api-version', '/api/version')
    config.add_route('api-people-list', '/api/people')
    config.add_route('api-people-get', '/api/people/{key}/{value}')
    config.add_route('api-group-list', '/api/groups')
    config.add_route('api-group-create', '/api/group/create')
    config.add_route('api-group-get', '/api/group/{key}/{value}')
    config.add_route('api-group-membership',
                     '/api/group/{gid}/membership/grant/{uid}')
    config.add_route('api-group-role', '/api/group/membership/edit/{mid}')
    config.add_route('api-group-types', '/api/group/types')

    # API private requests
    config.add_route('api-request-login', '/api/request-login')
    config.add_route('api-request-perms', '/api/request-perm/{scope}')

    # Settings pages
    config.add_route('settings', '/settings')
    config.add_route('captcha-image', '/settings/captcha/{cipherkey}')

    config.add_route('lost-password', '/settings/lost/password')
    config.add_route('reset-password',
                     '/settings/reset/password/{username}/{token}')

    # management calls
    config.add_route('lock', '/settings/lock/{context}/{id}')
    config.add_route('unlock', '/settings/unlock/{context}/{id}')
    config.add_route('archive', '/settings/archive/{context}/{id}')
    config.add_route('disable', 'settings/disable/{context}/{id}')
    config.add_route('enable', '/settings/enable/{context}/{id}')

    config.add_route('add-group', '/settings/add/group')
    config.add_route('remove-group', '/settings/remove/group/{id}')

    config.add_route('add-license', '/settings/add/license')
    config.add_route('edit-license', '/settings/edit/license/{id}')
    config.add_route('remove-license', '/settings/remove/license/{id}')
    config.add_route('sign-license', '/settings/sign/license/{id}')

    config.add_route('add-grouptype', '/settings/add/group/type')
    config.add_route('edit-grouptype', '/settings/edit/group/type/{id}')
    config.add_route('remove-grouptype', '/settings/remove/group/type/{id}')

    config.add_route('add-certificate', '/settings/add/certificate')
    config.add_route('edit-certificate', '/settings/edit/certificate/{id}')
    config.add_route('remove-certificate', '/settings/remove/certificate/{id}')
    config.add_route('get-client-cert', '/settings/create/client-certificate')

    config.add_route('dump-data', '/settings/dump/{key}')  # internal query

    config.scan()
    config.add_subscriber(add_renderer_globals, BeforeRender)

    return config.make_wsgi_app()
