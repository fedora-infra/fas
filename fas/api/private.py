# -*- coding: utf-8 -*-
#
# Copyright © 2015 Xavier Lamien.
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
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from pyramid.view import view_config
from pyramid.security import remember

from fas.api import MetaData
from fas.security import ParamsValidator, get_auth_scopes
from fas.security import process_login
from fas.security import LoginStatus
from fas.security import SignedDataValidator
from fas.events import ApiRequest
from fas.models import provider, register


class PrivateRequest(object):
    def __init__(self, request):
        self.request = request
        self.notify = self.request.registry.notify
        self.params = ParamsValidator(self.request, True)
        self.data = MetaData('RequestResult')
        self.perm = None

        self.notify(ApiRequest(
            self.request, self.data, self.perm, is_private=True)
        )

        self.sdata = None
        # self.sdata = SignedDataValidator(
        #     self.request.json_body['credentials'],
        #     self.request.token_validator.get_obj().secret
        # )

    @view_config(
        route_name='api-request-login', renderer='json', request_method='POST'
    )
    def request_login(self):
        auth_response = {}
        self.sdata = SignedDataValidator(
            self.request.json_body['credentials'],
            self.request.token_validator.get_obj().secret
        )

        if self.sdata.validate():
            login = self.sdata.get_data()['login']
            password = self.sdata.get_data()['password']

            person = provider.get_people_by_username(login)

            result = process_login(self.request, person, password)

            auth_response['LoginStatus'] = result.value

            if result == LoginStatus.SUCCEED:
                headers = remember(self.request, person.username)
                auth_response['Scope'] = get_auth_scopes()
                auth_response['Data'] = self.sdata.sign_data(
                    {'auth_token': headers[0][1]}
                )
                self.data.set_data(auth_response)
            elif result == LoginStatus.FAILED_INACTIVE_ACCOUNT:
                self.data.set_error_msg('Access denied', 'Inactive account')
            elif result == LoginStatus.FAILED_LOCKED_ACCOUNT:
                self.data.set_error_msg('Access denied', 'Account locked')
            else:
                self.data.set_error_msg(
                    'Access denied', 'Login or password error')

        self.data.set_data(auth_response)
        return self.data.get_metadata()

    @view_config(
        route_name='api-request-perms', renderer='json', request_method='POST',
        permission='authenticated'
    )
    def request_permissions(self):
        self.sdata = SignedDataValidator(
            self.request.json_body['credentials'],
            self.request.token_validator.get_obj().secret
        )
        scope = self.request.matchdict.get('scope')
        auth_scope = [scp for scp in get_auth_scopes() if scp['name'] == scope]

        if self.sdata.validate():
            data = self.sdata.get_data()
            if 'token' in data and len(auth_scope) > 0:
                auth_scope = auth_scope[0]
                register.add_token(
                    description=data['name'],
                    permission=auth_scope['permission'],
                    token=data['token'],
                    people_id=self.request.get_user.id
                )
                self.data.set_data({'Message': 'Permission granted'})
            else:
                self.data.set_error_msg('Invalid key', 'Unknown scope: %s' % scope)
        else:
            self.data.set_error_msg(
                self.sdata.get_msg()[0],
                self.sdata.get_msg()[1]
            )

        return self.data.get_metadata()

    def revoke_permissions(self):
        pass