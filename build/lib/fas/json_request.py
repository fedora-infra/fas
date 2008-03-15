import turbogears
from turbogears import controllers, expose, identity 

import sqlalchemy

from fas.model import People
from fas.model import Groups
from fas.model import Log

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
            return dict(success=True, group=group)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json", allow_json=True)
    def group_by_name(self, groupname):
        try:
            group = Groups.by_name(groupname)
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

