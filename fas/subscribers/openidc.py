# -*- coding: utf-8 -*-
#
# Copyright © 2016 Xavier Lamien.
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

import requests
import logging

from pyramid.events import subscriber

from fas import release
from fas.events import TokenValidationRequest
from fas.models import provider
from fas.security import get_auth_scopes
from fas.util import Config

log = logging.getLogger(__name__)


@subscriber(TokenValidationRequest)
def on_token_validation_request(event):
    """
    Validate OpenIDConnect token on request.

    :param event: The pyramid event
    :type event: pyramid.event
    """
    if Config.get("token.engine") != "openidc":
        return

    apikey = event.request.token_validator
    """:type: fas.security.TokenValidator"""
    scopes = get_auth_scopes()

    payload = {
        "token": apikey.token,
        "token_type_hint": Config.get("openidc.token_type"),
        "client_id": Config.get("openidc.client_id"),
        "client_secret": Config.get("openidc.secret")
    }
    headers = {
        "User-Agent": "{0:s} ({1:s}) {2:s}/{3:s}".format(
            Config.get("project.name"),
            Config.get("project.organization"),
            release.__NAME__,
            release.__VERSION__
        )
    }

    request_url = Config.get("openidc.baseurl") + "/TokenInfo"

    try:
        response = requests.post(request_url, headers=headers, data=payload)
        response.raise_for_status()
    except (requests.ConnectionError, requests.Timeout) as e:
        log.error(u"Unable to request tokenInfo. {0:s}".format(e))
    except requests.HTTPError as e:
        log.error(e)

    token_info = response.json()

    if token_info["active"]:
        if "sub" in token_info:
            person = provider.get_people_by_username(token_info["sub"])

            if person and token_info["scope"] in [s["name"] for s in scopes]:
                apikey.valid_token = True
                for s in scopes:
                    if s["name"] == token_info["scope"]:
                        apikey.permission = s["permission"]
    else:
        log.error(u"Invalid or expired token")

