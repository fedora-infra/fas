from pyramid.config import Configurator

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config

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
        settings=settings
        )

    config.include('pyramid_mako')

    config.add_mako_renderer('.xhtml', settings_prefix='mako.')

    config.add_static_view('static', 'fas:static/theme/%s'
                            % settings['project.name'],
                            cache_max_age=int(settings['cache.max_age'])
                            )

    authn_policy = AuthTktAuthenticationPolicy(
        settings['authtkt.secret'],
        hashalg='sha512'
        )

    authz_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.add_translation_dirs('fas:locale/')

    #config.add_subscriber('fas.subscribers.add_renderer_globals',
    #                      'pyramid.events.BeforeRender')
    #config.add_subscriber('fas.subscribers.i18n.add_localizer',
    #                      'pyramid.events.NewRequest')

    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.add_route('items-paging', '/{item}/list/{page}')

    config.add_route('people', '/people')
    config.add_route('people-paging', '/people/page/{pagenb}')
    config.add_route('people-profile', '/people/profile/{id}')
    config.add_route('people-activities', '/people/profile/{id}/activities')

    config.add_route('groups', '/groups')
    config.add_route('groups-paging', '/groups/page/{pagenb}')
    config.add_route('group-details', '/group/details/{id}')

    config.add_route('api_home', '/api')
    config.add_route('api_people_list', '/api/people')
    config.add_route('api_people_get', '/api/people/{key}/{value}')
    config.add_route('api_group_list', '/api/group')
    config.add_route('api_group_get', '/api/group/{key}/{value}')

    config.scan()
    return config.make_wsgi_app()
