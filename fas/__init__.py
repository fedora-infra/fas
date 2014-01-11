from pyramid.config import Configurator

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config

from models.models import (
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
    config.add_renderer('.xhtml', 'pyramid.mako_templating.renderer_factory')
    config.add_static_view('static', 'fas:static/theme/fedoraproject',
                            cache_max_age=3600)
    
    config.add_translation_dirs('fas:locale/')

    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.scan()
    return config.make_wsgi_app()
