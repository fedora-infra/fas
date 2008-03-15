import turbogears
from turbogears import controllers, expose, identity 

from fas.model import People
from fas.model import Groups
from fas.model import Log

from fas.auth import *

class JsonRequest(controllers.Controller):
    def __init__(self):
        """Create a JsonRequest Controller."""

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json")
    def index(self):
        """Return a help message"""
        return dict(help='This is a JSON interface.')

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json")
    def person_by_id(self, id):
        try:
            person = People.by_id(id)
            return dict(success=True, person=person)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json")
    def person_by_username(self, username):
        try:
            person = People.by_username(username)
            return dict(success=True, person=person)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json")
    def group_by_id(self, id):
        try:
            group = Groups.by_id(id)
            return dict(success=True, group=group)
        except InvalidRequestError:
            return dict(success=False)

    @identity.require(turbogears.identity.not_anonymous())
    @expose("json")
    def group_by_name(self, groupname):
        try:
            group = Groups.by_name(groupname)
            return dict(success=True, group=group)
        except InvalidRequestError:
            return dict(success=False)

