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
    my_session_factory = SignedCookieSessionFactory('secret')

    config = Configurator(session_factory = my_session_factory, settings=settings)

    config.include('pyramid_mako')

    config.add_mako_renderer('.xhtml', settings_prefix='mako.')
    config.add_static_view('static', 'fas:static/theme/fedoraproject',
                            cache_max_age=3600)

    config.add_translation_dirs('fas:locale/')

    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.scan()
    return config.make_wsgi_app()
