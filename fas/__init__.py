from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config

from .release import get_release_info

from .security import (
    groupfinder,
    authenticated_is_admin,
    authenticated_is_modo,
    authenticated_is_group_admin,
    authenticated_is_group_editor,
    authenticated_is_group_sponsor,
    request_membership,
    requested_membership
    )

from .models.provider import get_authenticated_user

from models import (
    DBSession,
    Base,
    )

import logging

log = logging.getLogger(__name__)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    from pyramid.session import SignedCookieSessionFactory
    my_session_factory = SignedCookieSessionFactory(
        settings['session.secret'],
        timeout=settings['session.timeout']
        )

    config = Configurator(
        session_factory=my_session_factory,
        settings=settings,
        root_factory='fas.security.Root'
        )

    config.include('pyramid_mako')

    config.add_mako_renderer('.xhtml', settings_prefix='mako.')

    config.add_static_view(
        'static', 'fas:static/theme/%s' % settings['project.name'],
        cache_max_age=int(settings['cache.max_age'])
    )

    authn_policy = AuthTktAuthenticationPolicy(
        settings['authtkt.secret'],
        hashalg='sha512',
        callback=groupfinder
        )

    authz_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.add_translation_dirs('fas:locale/')

    config.add_request_method(get_release_info, 'release', reify=True)
    config.add_request_method(get_authenticated_user, 'get_user', reify=True)
    config.add_request_method(
        authenticated_is_admin, 'authenticated_is_admin', reify=False)
    config.add_request_method(
        authenticated_is_modo, 'authenticated_is_modo', reify=False)
    config.add_request_method(
        authenticated_is_group_admin, 'authenticated_is_group_admin',
        reify=False)
    config.add_request_method(
        authenticated_is_group_editor, 'authenticated_is_group_editor',
        reify=False)
    config.add_request_method(
        authenticated_is_group_sponsor, 'authenticated_is_group_sponsor',
        reify=False)
    config.add_request_method(
        request_membership, 'request_membership', reify=False)
    config.add_request_method(
        requested_membership, 'requested_membership', reify=False)

    # home pages
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    # People pages
    config.add_route('people', '/people')
    config.add_route('people-new', '/people/new')
    config.add_route('people-confirm-account', 'people/confirm/{token}')
    config.add_route('people-lost-password', 'people/lost/password')
    config.add_route('people-reset-password', 'people/reset/password/{token}')
    config.add_route('people-paging', '/people/page/{pagenb}')
    config.add_route('people-profile', '/people/profile/{id}')
    config.add_route('people-activities', '/people/profile/{id}/activities')
    config.add_route('people-token', '/people/profile/{id}/accesstoken')
    config.add_route('people-edit', '/people/profile/{id}/edit')
    config.add_route('people-password', '/people/profile/{id}/edit/password')

    # Grops pages
    config.add_route('groups', '/groups')
    config.add_route('groups-paging', '/groups/page/{pagenb}')
    config.add_route('group-details', '/group/details/{id}')
    config.add_route('group-edit', '/group/details/{id}/edit')

    # API requests
    config.add_route('api_home', '/api')
    config.add_route('api_people_list', '/api/people')
    config.add_route('api_people_get', '/api/people/{key}/{value}')
    config.add_route('api_group_list', '/api/group')
    config.add_route('api_group_get', '/api/group/{key}/{value}')

    # Settings pages
    config.add_route('settings', '/settings')

    config.add_route('add-group', '/settings/add/group')
    config.add_route('remove-group', '/settings/remove/group/{id}')

    config.add_route('add-license', '/settings/add/license')
    config.add_route('edit-license', '/settings/edit/license')
    config.add_route('remove-license', '/settings/remove/license/{id}')

    config.add_route('add-grouptype', '/settings/add/group/type')
    config.add_route('edit-grouptype', '/settings/edit/group/type/{id}')
    config.add_route('remove-grouptype', '/settings/remove/group/type/{id}')

    config.scan()
    return config.make_wsgi_app()
