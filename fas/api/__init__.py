# -*- coding: utf-8 -*-

from pyramid.response import Response
from pyramid.view import view_config

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

import fas.forms as forms
from fas.models import DBSession, AccountStatus
import fas.models.provider as provider


class BadRequest(Exception):
    pass


class NotFound(Exception):
    pass


@view_config(route_name='api_home', renderer='/api_home.xhtml')
def api_home(request):
    return {}


def __get_user(key, value):
    if key not in ['id', 'username', 'email', 'ircnick']:
        raise BadRequest(
            {"error": "Bad request, no '%s' allowed" % key}
        )
    method = getattr(provider, 'get_people_by_%s' % key)
    user = method(DBSession, value)
    if not user:
        raise NotFound(
            {"error": "No such user %r" % value}
        )

    return user


def __get_group(key, value):
    if key not in ['id', 'name']:
        raise BadRequest(
            {"error": "Bad request, no '%s' allowed" % key}
        )
    method = getattr(provider, 'get_group_by_%s' % key)
    group = method(DBSession, value)
    if not group:
        raise NotFound(
            {"error": "No such group %r" % value}
        )

    return group


@view_config(route_name='api_user_get', renderer='json', request_method='GET')
def api_user_get(request):
    key = request.matchdict.get('key')
    value = request.matchdict.get('value')
    try:
        user = __get_user(key, value)
    except BadRequest as err:
        request.response.status = '400 bad request'
        return err
    except NotFound as err:
        request.response.status = '404 page not found'
        return err

    return user.to_json()


@view_config(route_name='api_group_get', renderer='json', request_method='GET')
def api_group_get(request):
    key = request.matchdict.get('key')
    value = request.matchdict.get('value')
    try:
        group = __get_group(key, value)
    except BadRequest as err:
        request.response.status = '400 bad request'
        return err
    except NotFound as err:
        request.response.status = '404 page not found'
        return err

    return group.to_json()

