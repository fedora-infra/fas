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
from turbogears import controllers, expose, identity

import sqlalchemy

from fas.model import People
from fas.model import Groups
from fas.model import Log
from fas.model import BugzillaQueue

from fas.auth import *

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
        try:
            person = People.by_id(id)
            person.jsonProps = {
                    'People': ('approved_memberships', 'unapproved_memberships')
                    }
            return dict(success=True, person=person)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def person_by_username(self, username):
        try:
            person = People.by_username(username)
            person.jsonProps = {
                'People': ('approved_memberships', 'unapproved_memberships')
                }
            return dict(success=True, person=person)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def group_by_id(self, id):
        try:
            group = Groups.by_id(id)
            group.jsonProps = {'Groups': ('approved_roles', 'unapproved_roles')}
            return dict(success=True, group=group)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def group_by_name(self, groupname):
        try:
            group = Groups.by_name(groupname)
            group.jsonProps = {'Groups': ('approved_roles', 'unapproved_roles')}
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

