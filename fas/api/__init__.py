# -*- coding: utf-8 -*-

#from pyramid.response import Response
from pyramid.view import view_config

#from sqlalchemy.exc import DBAPIError

#from pyramid.view import (
#    view_config,
#    forbidden_view_config,
#)

#from pyramid.security import (
#    remember,
#    forget,
#    authenticated_userid,
#)

#import fas.forms as forms
#from fas.models import DBSession, AccountStatus
#import fas.models.provider as provider


class BadRequest(Exception):
    pass


class NotFound(Exception):
    pass


@view_config(route_name='api_home', renderer='/api_home.xhtml')
def api_home(request):
    return {}

