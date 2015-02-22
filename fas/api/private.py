# -*- coding: utf-8 -*-

from pyramid.view import view_config

from fas.api import MetaData
from fas.security import ParamsValidator
from fas.security import process_login
from fas.security import LoginStatus
from fas.security import generate_token
from fas.security import SignedDataValidator
from fas.events import ApiRequest
from fas.models import provider


class PrivateRequest(object):
    def __init__(self, request):
        self.request = request
        self.notify = self.request.registry.notify
        self.params = ParamsValidator(self.request, True)
        self.data = MetaData('Reply')
        self.perm = None

        self.notify(ApiRequest(
            self.request, self.data, self.perm, is_private=True)
        )

        self.sdata = SignedDataValidator(
            self.request.json_body['data'],
            self.request.token_validator.get_obj().secret
        )

    @view_config(
        route_name='api-request-login', renderer='json', request_method='POST'
    )
    def request_login(self):
        answer = {}

        if self.sdata.validate():
            login = self.sdata.get_data()['login']
            password = self.sdata.get_data()['password']

            person = provider.get_people_by_username(login)

            result = process_login(self.request, person, password)

            if result == LoginStatus.SUCCEED:
                auth_tk = {'auth_tk': generate_token()}
                answer = {'status': result,
                          'data': SignedDataValidator.sign_data(auth_tk)}
                # TODO: provide a list of allowed perms to request
                # TODO: if requester if not a trusted app
                self.data.set_data(answer)
            elif result == LoginStatus.SUCCEED_NEED_APPROVAL:
                answer = {'status': 'need_approval'}
            elif result == LoginStatus.FAILED_INACTIVE_ACCOUNT:
                answer = {'status': 'failed'}
                self.data.set_error_msg('Access denied', 'Inactive account')
            elif result == LoginStatus.FAILED_LOCKED_ACCOUNT:
                answer = {'status': 'failed'}
                self.data.set_error_msg('Access denied', 'Account locked')
            else:
                answer = {'status': result}
                self.data.set_error_msg(
                    'Access denied', 'Login or password error')

        self.data.set_data(answer)
        return self.data.get_metadata()

    @view_config(
        route_name='api-request-perms', renderer='json', request_method='GET'
    )
    def request_permissions(self):
        pass
        # perm = self.request.json_body['scope']


    def revoke_permissions(self):
        pass