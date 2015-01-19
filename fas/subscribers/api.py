# -*- coding: utf-8 -*-

from pyramid.events import subscriber
from pyramid.response import Response
from pyramid.httpexceptions import HTTPUnauthorized, HTTPBadRequest

from fas.api import BadRequest
from fas.events import ApiRequest, TokenUsed

from fas.security import TokenValidator
from pyramid.view import view_config
import datetime
import logging

log = logging.getLogger(__name__)


@subscriber(ApiRequest)
def on_api_request(event):
    """ API requests listener. """
    params = event.params
    data = event.data

    # Check parameters and API key validities on every single API requests
    if params.is_valid():
        apikey = TokenValidator(params.get_apikey())
        if apikey.is_valid():
            event.perm = apikey.get_perm()
            apikey.get_obj().last_used = datetime.datetime.utcnow()
        else:
            log.debug('Given API key is invalid.')
            data.set_error_msg(apikey.get_msg()[0], apikey.get_msg()[1])
            raise HTTPUnauthorized(
                body=unicode(data.get_metadata()),
                content_type='application/json')
    else:
        log.error('Parameters are missing from this request.')
        data.set_error_msg(params.get_msg()[0], params.get_msg()[1])
        raise HTTPBadRequest(
            body=unicode(data.get_metadata()),
            content_type='application/json')


@subscriber(TokenUsed)
def on_token_used(event):
    """ Token activity listener. """
    event.perm.last_used = datetime.datetime.utcnow()

    log.debug('Saving token last usage timestamp for user %s',
        event.person.username)

