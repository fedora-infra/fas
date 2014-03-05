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


@view_config(route_name='api_user_get', renderer='json', request_method='POST')
def api_user_edit(request):
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

    form = forms.EditPeopleForm(request.POST)
    if form.validate():
        # Handle the latitude longitude that needs to be number or None
        form.latitude.data = form.latitude.data or None
        form.longitude.data = form.longitude.data or None

        # Convert the status provided as string into an integer
        #status = provider.get_accountstatus_by_status(
        #    DBSession, status=form.status.data)
        #if not status:
        #    request.response.status = '400 bad request'
        #    return {'error': 'Invalid status provided'}

        #form.status.data = status
        form.populate_obj(user)
        DBSession.add(user)
        return {'message': 'User updated', 'user': user.to_json()}
    else:
        request.response.status = '400 bad request'
        return {'error': 'Invalid request', 'messages': form.errors}