# -*- coding: utf-8 -*-

from . import (
    BadRequest,
    NotFound
    )

from pyramid.response import Response
from pyramid.view import view_config

from pyramid.view import (
    view_config,
    forbidden_view_config,
)

import fas.forms as forms
from fas.models import DBSession, AccountStatus
import fas.models.provider as provider


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