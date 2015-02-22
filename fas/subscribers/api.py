# -*- coding: utf-8 -*-

import datetime

from pyramid.events import subscriber
from pyramid.httpexceptions import HTTPUnauthorized, HTTPBadRequest

from fas import log
from fas.events import ApiRequest, TokenUsed
from fas.security import SignedDataValidator


@subscriber(ApiRequest)
def on_api_request(event):
    """
    API requests listener which:
     check parameters and API key validity on every
     single API request.

     Also check for private API request if any.
    """
    params = event.request.param_validator
    data = event.data
    request = event.request

    ct_type = 'application/json'
    apikey = None

    if params.validate():
        apikey = event.request.token_validator
        if apikey.validate():
            event.perm = apikey.get_perm()
            # Update token activity
            apikey.get_obj().last_used = datetime.datetime.utcnow()
        else:
            log.debug('Given API key is invalid.')
            data.set_error_msg(apikey.get_msg()[0], apikey.get_msg()[1])
            raise HTTPUnauthorized(
                body=unicode(data.get_metadata()),
                content_type=ct_type
            )
    else:
        log.error('Missing parameters from this request.')
        data.set_error_msg(params.get_msg()[0], params.get_msg()[1])
        raise HTTPBadRequest(
            body=unicode(data.get_metadata()),
            content_type=ct_type
        )

    # Check private request
    if event.is_private:
        log.debug('Parsing request for signed data:\n %s' % request.json_body)
        sdata = SignedDataValidator(
            request.json_body['data'],
            secret=apikey.get_obj().secret
        )
        if not sdata.validate():
            data.set_error_msg(sdata.get_msg[0], sdata.get_msg[1])
            raise HTTPBadRequest(
                body=unicode(data.get_metadata()),
                content_type=ct_type
            )


@subscriber(TokenUsed)
def on_token_used(event):
    """ Token activity listener. """
    event.perm.last_used = datetime.datetime.utcnow()

    log.debug('Saving token last usage timestamp for user %s',
              event.person.username)

