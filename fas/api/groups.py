# -*- coding: utf-8 -*-

from . import (
    BadRequest,
    NotFound,
    MetaData
    )

from pyramid.view import view_config

import fas.models.provider as provider

from fas.events import ApiRequest

from fas.security import TokenValidator
from fas.security import ParamsValidator


class GroupAPI(object):

    def __init__(self, request):
        self.request = request
        self.notify = self.request.registry.notify
        self.params = ParamsValidator(self.request, True)
        self.data = MetaData('Groups')
        self.perm = None
        self.notify(ApiRequest(self.request, self.data, self.params,self.perm))
        self.apikey = TokenValidator(self.params.get_apikey())

    def __get_group__(self, key, value):
        if key not in ['id', 'name']:
            raise BadRequest('Invalid key: %s' % key)
        method = getattr(provider, 'get_group_by_%s' % key)
        group = method(value)
        if not group:
            raise NotFound('No such group: %s' % value)

        return group

    @view_config(
        route_name='api_group_list', renderer='json', request_method='GET')
    def group_list(self):
        """ Returns a JSON's output of registered group's list. """
        group = None

        self.params.add_optional('limit')
        self.params.add_optional('page')

        if self.apikey.is_valid():
            limit = self.params.get_limit()
            page = self.params.get_pagenumber()

            group = provider.get_groups(limit=limit, page=page)

        if group:
            groups = []
            for g in group:
                groups.append(g.to_json(self.apikey.get_perm()))

            self.data.set_pages(provider.get_groups(count=True), page, limit)
            self.data.set_data(groups)

        return self.data.get_metadata()

    @view_config(route_name='api_group_get', renderer='json', request_method='GET')
    def api_group_get(self):
        group = None

        if self.apikey.is_valid():
            key = self.request.matchdict.get('key')
            value = self.request.matchdict.get('value')

            try:
                group = self.__get_group__(key, value)
            except BadRequest as err:
                self.request.response.status = '400 bad request'
                self.data.set_error_msg('Bad request', err.message)
            except NotFound as err:
                self.data.set_error_msg('Item not found', err.message)
                self.request.response.status = '404 page not found'

        if group:
            self.data.set_data(group.to_json(self.apikey.get_perm()))

        return self.data.get_metadata()
