# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou
# Copyright © 2008-2009 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
#            Toshio Kuratomi <toshio@redhat.com>
#
import turbogears
from turbogears import controllers, expose, identity, config

from sqlalchemy.exc import InvalidRequestError
import sqlalchemy
from sqlalchemy import select

from fas.model import People
from fas.model import Groups
from fas.model import PersonRoles
from fas.model import PeopleTable
from fas.model import GroupsTable
from fas.model import PersonRolesTable

import memcache

# TODO: Should this code be put somewhere else?
memcached_servers = config.get('memcached_server').split(',')
# Setup our memcache client
mc = memcache.Client(memcached_servers)

class JsonRequest(controllers.Controller):
    def __init__(self):
        """Create a JsonRequest Controller."""

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def index(self):
        """Return a help message"""
        return dict(help='This is a JSON interface.')

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def person_by_id(self, person_id):
        try:
            person = People.by_id(person_id)
            person_data = person.filter_private()
            person_data['approved_memberships'] = list(person.approved_memberships)
            person_data['unapproved_memberships'] = list(person.unapproved_memberships)
            return dict(success=True, person=person_data)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def fas_client(self, data=None, force_refresh=None):
        admin_group = config.get('admingroup', 'accounts')
        system_group = config.get('systemgroup', 'fas-system')
        thirdparty_group = config.get('thirdpartygroup', 'thirdparty')

        privs = {
            'admin': False,
            'system': False,
            'thirdparty': False,
        }

        if identity.in_group(admin_group):
            privs['admin'] = privs['system'] = privs['thirdparty'] = True
        elif identity.in_group(system_group):
            privs['system'] = privs['thirdparty'] = True
        elif identity.in_group(thirdparty_group):
            privs['thirdparty'] = True

        if data == 'group_data':
            groups = None
            if not force_refresh:
                groups = mc.get('group_data')
            if not groups:
                groups = {}
                groupjoin = [GroupsTable.outerjoin(PersonRolesTable,
                    PersonRolesTable.c.group_id == GroupsTable.c.id)]

                group_query = select([GroupsTable.c.id, GroupsTable.c.name,
                    GroupsTable.c.group_type, PersonRolesTable.c.person_id,
                    PersonRolesTable.c.role_status, PersonRolesTable.c.role_type],
                    from_obj=groupjoin)

                results = group_query.execute()

                for id, name, group_type, person_id, role_status, role_type in results:
                    if name not in groups:
                        groups[name] = {
                            'id': id,
                            'administrators': [],
                            'sponsors': [],
                            'users': [],
                            'type': group_type
                        }

                    if role_status != 'approved':
                        continue

                    if role_type == 'administrator':
                        groups[name]['administrators'].append(person_id)
                    elif role_type == 'sponsor':
                        groups[name]['sponsors'].append(person_id)
                    elif role_type == 'user':
                        groups[name]['users'].append(person_id)

                # Save cache - valid for 15 minutes
                mc.set('group_data', groups, 900)

            return dict(success=True, data=groups)
        elif data == 'user_data':
            people = {}
            people_list = select([
                PeopleTable.c.id,
                PeopleTable.c.username,
                PeopleTable.c.password,
                PeopleTable.c.human_name,
                PeopleTable.c.ssh_key,
                PeopleTable.c.email,
                PeopleTable.c.privacy,
                PeopleTable.c.alias_enabled
                ], PeopleTable.c.status == 'active').execute()
            for id, username, password, human_name, ssh_key, email, privacy, alias_enabled in people_list:
                people[id] = {
                    'username': username,
                    'password': password,
                    'human_name': human_name,
                    'ssh_key': ssh_key,
                    'email': email,
                    'alias_enabled': alias_enabled
                }

                if privacy:
                    # If they have privacy enabled, set their human_name to
                    # their username
                    people[id]['human_name'] = username

                if not privs['system']:
                    people[id]['password'] = '*'
                if not privs['thirdparty']:
                    people[id]['ssh_key'] = ''
            return dict(success=True, data=people)
        return dict(success=False, data={})

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def person_by_username(self, username):
        try:
            person = People.by_username(username)
            person_data = person.filter_private()
            person_data['approved_memberships'] = list(person.approved_memberships)
            person_data['unapproved_memberships'] = list(person.unapproved_memberships)
            return dict(success=True, person=person_data)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def group_by_id(self, group_id):
        try:
            group = Groups.by_id(group_id)
            group.json_props = {
                    'Groups': ('approved_roles', 'unapproved_roles')}
            return dict(success=True, group=group)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def group_by_name(self, groupname):
        try:
            group = Groups.by_name(groupname)
            group.json_props = {
                    'Groups': ('approved_roles', 'unapproved_roles')}
            return dict(success=True, group=group)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def user_id(self):
        people = {}
        peoplesql = sqlalchemy.select([People.id, People.username])
        persons = peoplesql.execute()
        for person in persons:
            people[person[0]] = person[1]
        return dict(people=people)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def people_query(self, columns=None, **constraints):
        people_columns = [c.name for c in PeopleTable.columns]

        # Queryable columns are temporarily limited until
        # privacy filtering is implemented for this method.
        column_map = {
            'id': PeopleTable.c.id,
            'username': PeopleTable.c.username,
            #'human_name': PeopleTable.c.human_name,
            #'gpg_keyid': PeopleTable.c.gpg_keyid,
            #'ssh_key': PeopleTable.c.ssh_key,
            'email': PeopleTable.c.email,
            #'country_code': PeopleTable.c.country_code,
            #'creation': PeopleTable.c.creation,
            'ircnick': PeopleTable.c.ircnick,
            'status': PeopleTable.c.status,
            #'locale': PeopleTable.c.locale,
            #'timezone': PeopleTable.c.timezone,
            #'latitude': PeopleTable.c.latitude,
            #'longitude': PeopleTable.c.longitude,
            'group': GroupsTable.c.name,
            'group_type': GroupsTable.c.group_type,
            'role_status': PersonRolesTable.c.role_status,
            'role_type': PersonRolesTable.c.role_type,
            'role_approval': PersonRolesTable.c.approval,
        }

        if columns:
            cols = columns.split(',')
        else:
            # By default, return all of the people columns in column_map.
            cols = [c for c in people_columns if c in column_map]

        print cols
        print constraints

        groupjoin = []
        if 'group' in constraints \
            or 'group_type' in constraints \
            or 'role_status' in constraints \
            or 'role_type' in constraints:
            groupjoin = [PeopleTable.join(PersonRolesTable,
                PersonRolesTable.c.person_id == PeopleTable.c.id).join(GroupsTable,
                GroupsTable.c.id == PersonRolesTable.c.group_id)]

        try:
            query = select([column_map[c] for c in cols], from_obj=groupjoin)
        except KeyError:
            return dict(success=False, error='Invalid column requested.', data={})

        for k, v in constraints.iteritems():
            if k not in column_map:
                return dict(success=False,
                error='Invalid constraint specified.', data={})
            query = query.where(column_map[k].like(v))

        results = [dict(zip(cols, r)) for r in query.execute()]
        return dict(success=True, data=results)
