# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou All rights reserved.
# Copyright © 2008 Red Hat, Inc. All rights reserved.
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
#
import turbogears
from turbogears import controllers, expose, identity, config

from sqlalchemy.exceptions import InvalidRequestError
import sqlalchemy
from sqlalchemy import select
from sqlalchemy.orm import eagerload

from fas.model import People
from fas.model import Groups
from fas.model import PersonRoles
from fas.model import PeopleTable

import cPickle as pickle
from time import time
import os

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
    def person_by_id(self, id):
        ### FIXME: we should rename id => userid as id is a builtin
        userid = id
        del id

        try:
            person = People.by_id(userid)
            person.json_props = {
                    'People': ('approved_memberships', 'unapproved_memberships')
                    }
            person.filter_private()
            return dict(success=True, person=person)
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
            groups = {}

            try:
                cache_age = time() - os.path.getctime('/var/tmp/groups.pkl')
                if not force_refresh or cache_age < 600:
                    f = open('/var/tmp/groups.pkl', 'r')
                    groups = pickle.load(f)
                    f.close()
            except (OSError, IOError, pickle.PickleError):
                pass

            if not groups:
                groups_list = Groups.query.options(eagerload('approved_roles')).all()
                for group in groups_list:
                    groups[group.name] = {
                        'id': group.id,
                        'administrators': [],
                        'sponsors': [],
                        'users': [],
                        'type': group.group_type
                    }

                    for role in group.approved_roles:
                        if role.role_type == 'administrator':
                            groups[group.name]['administrators'].append(role.person_id)
                        elif role.role_type == 'sponsor':
                            groups[group.name]['sponsors'].append(role.person_id)
                        elif role.role_type == 'user':
                            groups[group.name]['users'].append(role.person_id)

                # Save pickle cache
                f = open('/var/tmp/groups.pkl', 'w')
                pickle.dump(groups,f)
                f.close()

            return dict(success=True, data=groups)
        elif data == 'user_data':
            people = {}

            try:
                cache_age = time() - os.path.getctime('/var/tmp/users.pkl')
                if not force_refresh or cache_age < 600:
                    f = open('/var/tmp/users.pkl', 'r')
                    people = pickle.load(f)
                    f.close()
                    return dict(success=True, data=people)
              except (OSError, IOError, pickle.PickleError):
                  pass

            if not people:
                people_list = select([
                    PeopleTable.c.id,
                    PeopleTable.c.username,
                    PeopleTable.c.password,
                    PeopleTable.c.human_name,
                    PeopleTable.c.ssh_key,
                    PeopleTable.c.email,
                    PeopleTable.c.privacy,
                    ], PeopleTable.c.status == 'active').execute().fetchall();
                for person in people_list:
                    id = person[0]
                    username = person[1]
                    password = person[2]
                    human_name = person[3]
                    ssh_key = person[4]
                    email = person[5]
                    privacy = person[6]

                    people[id] = {
                        'username': username,
                        'password': password,
                        'human_name': human_name,
                        'ssh_key': ssh_key,
                        'email': email,
                    }

                    if privacy:
                        # If they have privacy enabled, set their human_name to
                        # their username
                        people[id]['human_name'] = username

                # Save pickle cache
                f = open('/var/tmp/users.pkl', 'w')
                pickle.dump(people,f)
                f.close()

        for person in people:
            if not privs['system']:
                people[person]['password'] = '*'
            if not privs['thirdparty']:
                people[person]['ssh_key'] = ''

        return dict(success=True, data=people)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def person_by_username(self, username):
        try:
            person = People.by_username(username)
            person.json_props = {
                'People': ('approved_memberships', 'unapproved_memberships')
                }
            person.filter_private()
            return dict(success=True, person=person)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def group_by_id(self, id):
        ### FIXME: we should rename id => groupid as id is a builtin
        groupid = id
        del id

        try:
            group = Groups.by_id(groupid)
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
        peoplesql = sqlalchemy.select([People.c.id, People.c.username])
        persons = peoplesql.execute()
        for person in persons:
            people[person[0]] = person[1]
        return dict(people=people)

