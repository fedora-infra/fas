# -*- coding: utf-8 -*-

from fas.api import (
    BadRequest,
    NotFound,
    MetaData
    )

from pyramid.response import Response
from pyramid.view import view_config

import fas.forms as forms
import fas.models.provider as provider
import fas.models.register as register

from fas.models import AccountPermissionType as perms

from fas.security import TokenValidator
from fas.security import ParamsValidator


def __get_user(key, value):
    if key not in ['id', 'username', 'email', 'ircnick']:
        raise BadRequest(
            {"error": "Bad request, no '%s' allowed" % key}
        )
    method = getattr(provider, 'get_people_by_%s' % key)
    user = method(value)
    if not user:
        raise NotFound(
            {"error": "No such user %r" % value}
        )

    return user

@view_config(route_name='api_people_list', renderer='json', request_method='GET')
def people_list(request):
    """ Returns a JSON's output of people's list. """
    people = None

    data = MetaData('People')

    param = ParamsValidator(request, True)
    param.add_optional('limit')
    param.add_optional('page')

    if param.is_valid():

        limit = param.get_limit()
        page = param.get_pagenumber()

        ak = TokenValidator(param.get_apikey())
        if ak.is_valid():
            people = provider.get_people(limit=limit, page=page)
        else:
            data.set_error_msg(ak.get_msg()[0], ak.get_msg()[1])
    else:
        data.set_error_msg(param.get_msg()[0], param.get_msg()[1])

    if people:
        users = []
        for user in people:
            users.append(user.to_json(perms.CAN_READ_PUBLIC_INFO))

        data.set_pages('people', page, limit)
        data.set_data(users)

    # Test insertion
    #register.save_account_activity(request, 3000, 1)

    return data.get_metadata()


@view_config(route_name='api_people_get', renderer='json', request_method='GET')
def api_user_get(request):
    user = None
    data = MetaData('People')
    param = ParamsValidator(request, True)

    if param.is_valid():
        ak = TokenValidator(param.get_apikey())
        if ak.is_valid():
            key = request.matchdict.get('key')
            value = request.matchdict.get('value')
            try:
                user = __get_user(key, value)
            except BadRequest as err:
                request.response.status = '400 bad request'
                return err
            except NotFound as err:
                request.response.status = '404 page not found'
                data.set_error_msg('Item not found',
                'Found no %s with the following value: %s' % (key, value))
        else:
            data.set_error_msg(ak.get_msg()[0], ak.get_msg()[1])
    else:
        data.set_error_msg(param.get_msg()[0], param.get_msg()[1])

    if user:
        data.set_data(user.to_json(ak.get_perms()))

    return data.get_metadata()


@view_config(route_name='api_people_get', renderer='json', request_method='POST')
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
        register.add_people(user)
        return {'message': 'User updated', 'user': user.to_json()}
    else:
        request.response.status = '400 bad request'
        return {'error': 'Invalid request', 'messages': form.errors}
