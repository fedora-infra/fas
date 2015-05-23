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
__author__ = ['Xavier Lamien <laxathom@fedoraproject.org>',
              'Pierre-Yves Chibon <pingou@fedoraproject.org>']

from pyramid.view import view_config

from . import (
    BadRequest,
    NotFound,
    MetaData,
    RequestStatus)
import fas.models.provider as provider
from fas.events import ApiRequest, GroupCreated
from fas.util import setup_group_form
from fas.models import register, AccountPermissionType, MembershipStatus
from fas import log


class GroupAPI(object):
    def __init__(self, request):
        self.request = request
        self.notify = self.request.registry.notify
        self.params = self.request.param_validator
        self.data = MetaData('Groups')

        self.notify(ApiRequest(self.request, self.data))
        self.apikey = self.request.token_validator

    def __get_group__(self, key, value):
        if key not in ['id', 'name']:
            raise BadRequest('Invalid key: %s' % key)
        method = getattr(provider, 'get_group_by_%s' % key)
        group = method(value)
        if not group:
            raise NotFound('No such group: %s' % value)

        return group

    def __requester_can_edit__(self):
        """
        :return: True if request can edit a group, otherwise false.
        :rtype: bool
        """
        if self.apikey.get_perm() >= AccountPermissionType.CAN_EDIT_GROUP_INFO:
            return True

        self.data.set_error_msg(self.apikey.get_msg())

        return False

    @view_config(
        route_name='api-group-list', renderer='json', request_method='GET')
    def group_list(self):
        """ Returns a JSON's output of registered group's list. """
        group = None

        self.params.add_optional('limit')
        self.params.add_optional('page')

        if self.apikey.validate():
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

    @view_config(route_name='api-group-get', renderer='json', request_method='GET')
    def get_group(self):
        group = None

        if self.apikey.validate():
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

    @view_config(
        route_name='api-group-types', renderer='json', request_method='GET')
    def get_group_type(self):
        group_types = provider.get_group_types()
        self.data.set_name('GroupTypes')

        if len(group_types) > 0:
            self.data.set_data([g.to_json() for g in group_types])
        else:
            self.data.set_error_msg('None items', 'No registered group\'s types.')

        return self.data.get_metadata()

    @view_config(
        route_name='api-group-get', renderer='json', request_method='POST')
    def edit_group(self):
        """
        Update group's information on remote client's request.
        """
        if not self.__requester_can_edit__():
            return self.data.get_metadata()

        key = self.request.matchdict.get('key')
        value = self.request.matchdict.get('value')

        try:
            group = self.__get_group__(key, value)
        except BadRequest as err:
            self.data.set_status(RequestStatus.FAILED.value)
            self.data.set_error_msg('Bad request', err.message)
        except NotFound as err:
            self.data.set_status(RequestStatus.FAILED.value)
            self.data.set_error_msg('Item not found', err.message)

        form = setup_group_form(self.request, group)

        if form.validate():
            form.populate_obj(group)
            self.data.set_status(RequestStatus.SUCCESS.value)
            self.data.set_data(group.to_json(self.apikey.get_perm()))
        else:
            self.data.set_status(RequestStatus.FAILED.value)
            self.data.set_error_msg('Invalid request', form.errors)

        return self.data.get_metadata()

    @view_config(
        route_name='api-group-create', renderer='json', request_method='POST')
    def create_group(self):
        """
        Create a group on remote client's request.
        """
        if not self.__requester_can_edit__():
            return self.data.get_metadata()

        form = setup_group_form(self.request)

        if form.validate():
            group = register.add_group(form)
            self.notify(GroupCreated(self.request, group))
            self.data.set_data(form.data)
            self.data.set_status(RequestStatus.SUCCESS.value)
        else:
            self.data.set_error_msg('Invalid data', form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    log.error('Error in field %s: %s' % (
                        getattr(form, field).label.text,
                        error
                    ))

        return self.data.get_metadata()

    def add_member(self):
        """
        Add member to given group on remote client's request.
        """
        pass

    def remove_member(self):
        """
        Remove member from a given group on remote client's request.
        """
        pass

    @view_config(
        route_name='api-group-membership', renderer='json', request_method='POST')
    def grant_membership(self):
        """
        Grants group's membership on remote client's request.
        """
        group_id = self.request.matchdict.get('gid')
        candidate_id = self.request.matchdict.get('uid')
        person = self.apikey.get_owner()
        param = 'sponsor'

        if not self.__requester_can_edit__():
            return self.data.get_metadata()

        if self.apikey.isTrusted:
            # Trusted 3rd party has to send us id of person who requested
            # membership approval we won't record membership or sponsorship on
            # behalf 3rd party.
            if self.request.json_body and \
                            param in self.request.json_body:
                sponsor = self.request.json_body[param]
            else:
                self.data.set_status(RequestStatus.FAILED.value)
                self.data.set_error_msg(
                    'Invalid param', 'Missing parameter %s' % param)
                return self.data.get_metadata()

        if person:
            sponsor = person.id

        membership = provider.get_membership_by_person_id(group_id, candidate_id)

        if membership:
            log.debug('Found membership for group %s' % membership.group.name)

            if membership.group and membership.group.requires_sponsorship:
                membership.sponsor = sponsor
            else:
                self.data.set_status(RequestStatus.FAILED.value)
                return self.data.get_metadata()

            membership.status = MembershipStatus.APPROVED
            self.data.set_status(RequestStatus.SUCCESS.value)
        else:
            self.data.set_status(RequestStatus.FAILED.value)
            self.data.set_error_msg('No Items',
                                    'Found no pending membership with '
                                    'group %s and person %s.' %
                                    (group_id, candidate_id))

        return self.data.get_metadata()

    def upgrade_membership(self):
        """
        Upgrade membership level from a given group on remote client's request.
        """
        pass

    def downgrade_membership(self):
        """
        Downgrade membership level from a given group on remote client's request.
        """
        pass

    def edit_membership(self):
        """
        Edit membership status from a given group on remote client's request.
        """
        pass