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

