# -*- coding: utf-8 -*-

from pyramid.response import Response
from pyramid.view import view_config

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
)

from sqlalchemy.exc import DBAPIError

from pyramid.view import (
    view_config,
    forbidden_view_config,
)

from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
)

from fas.models import DBSession
from fas.models.people import (
    People,
)

@view_config(route_name='api_home', renderer='/api_home.xhtml')
def api_home(request):
    return {}


@view_config(route_name='api_user_name', renderer='string')
def api_user_name(request):
    username = request.matchdict.get('username')
    if not username:
        raise HTTPNotFound(
            {"error": "Badly form request, no username provided"}
        )
    user = People.by_username(DBSession, username)
    if not user:
        raise HTTPNotFound(
            {"error": "No such user %r" % username}
        )

    return user.to_json()


@view_config(route_name='api_user_ircnick', renderer='string')
def api_user_ircnick(request):
    ircnick = request.matchdict.get('ircnick')
    if not ircnick:
        raise HTTPNotFound(
            {"error": "Badly form request, no ircnick provided"}
        )
    user = People.by_ircnick(DBSession, ircnick)
    if not user:
        raise HTTPNotFound(
            {"error": "No user found with the irnick %r" % ircnick}
        )

    return user.to_json()

