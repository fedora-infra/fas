# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Xavier Lamien.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# __author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

import datetime

from pyramid.events import subscriber
from pyramid.httpexceptions import HTTPUnauthorized, HTTPBadRequest

from fas import log
from fas.events import ApiRequest, TokenUsed
from fas.security import PrivateDataValidator


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
                body=unicode(data.get_metadata(format_json=True)),
                content_type=ct_type
            )
    else:
        log.error('Missing parameters from this request.')
        data.set_error_msg(params.get_msg()[0], params.get_msg()[1])
        raise HTTPBadRequest(
            body=unicode(data.get_metadata(format_json=True)),
            content_type=ct_type
        )

    # Check private request
    if request.method == 'POST' and event.is_private:
        log.debug('Parsing request for private data:\n %s' % request.json_body)
        pdata = PrivateDataValidator(
            request.json_body['credentials'],
            secret=apikey.get_obj().secret
        )
        if not pdata.validate():
            data.set_error_msg(pdata.get_msg[0], pdata.get_msg[1])
            raise HTTPBadRequest(
                body=unicode(data.get_metadata(format_json=True)),
                content_type=ct_type
            )


@subscriber(TokenUsed)
def on_token_used(event):
    """ Token activity listener. """
    event.perm.last_used = datetime.datetime.utcnow()

    log.debug('Saving token last usage timestamp for user %s',
              event.person.username)

