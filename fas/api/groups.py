# -*- coding: utf-8 -*-

from . import (
    BadRequest,
    NotFound,
    ParamsValidator,
    MetaData
    )

from pyramid.response import Response
from pyramid.view import view_config

from pyramid.view import (
    view_config,
    forbidden_view_config,
)

import fas.forms as forms
import fas.models.provider as provider

from fas.models import DBSession, AccountStatus
from fas.models import AccountPermissionType as perms
from fas.security import TokenValidator


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


@view_config(route_name='api_group_list', renderer='json', request_method='GET')
def group_list(request):
    """ Returns a JSON's output of registered group's list. """
    group = None
    data = MetaData('Groups')

    param = ParamsValidator(request)
    param.add_optional('limit')
    param.add_optional('page')

    if param.is_valid():

        limit = param.get_limit()
        page = param.get_pagenumber()

        ak = TokenValidator(DBSession, param.get_apikey())
        if ak.is_valid():
            group = provider.get_groups(
                DBSession,
                limit=limit,
                page=page
            )
        else:
            data.set_error_msg(ak.get_msg()[0], ak.get_msg()[1])
    else:
        data.set_error_msg(param.get_msg()[0], param.get_msg()[1])

    if group:
        groups = []
        for g in group:
            groups.append(g.to_json(perms.CAN_READ_PUBLIC_INFO))

        data.set_pages(page, limit, provider.get_groups_count(DBSession)[0])
        data.set_data(groups)

    return data.get_metadata()

@view_config(route_name='api_group_get', renderer='json', request_method='GET')
def api_group_get(request):
    group = None
    data = MetaData('Group')
    param = ParamsValidator(request)

    if param.is_valid():
        ak = TokenValidator(DBSession, param.get_apikey())
        if ak.is_valid():
            key = request.matchdict.get('key')
            value = request.matchdict.get('value')

            try:
                group = __get_group(key, value)
            except BadRequest as err:
                request.response.status = '400 bad request'
                return err
            except NotFound as err:
                data.set_error_msg('Item not found',
                'Found no %s with the following value: %s' % (key, value)
                )
                request.response.status = '404 page not found'
        else:
            data.set_error_msg(ak.get_msg()[0], ak.get_msg()[1])
    else:
        data.set_error_msg(param.get_msg()[0], param.get_msg()[1])

    if group:
        data.set_data(group.to_json(ak.get_perms))

    return data.get_metadata()
