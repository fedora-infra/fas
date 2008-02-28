import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import ldap
import cherrypy

import fas.fasLDAP

#from fas.fasLDAP import UserAccount
#from fas.fasLDAP import Person
#from fas.fasLDAP import Groups
#from fas.fasLDAP import UserGroup

from fas.auth import *

from fas.user import knownUser, usernameExists

from textwrap import dedent

import re

class JsonRequest(controllers.Controller):
    def __init__(self):
        '''Create a JsonRequest Controller.'''

    @expose("json")
    def index(self):
        '''Perhaps show a nice explanatory message about groups here?'''
        return dict(help='This is a json interface')
    
    @expose("json", allow_json=True)
    def group_list(self, search='*'):
        re_search = re.sub(r'\*', r'%', search).lower()
        groups = Groups.query.filter(Groups.name.like(re_search)).order_by('name')
        group_list = {}
        #return dict(groups=groups)
        for group in groups:
            group_list[group.id] = {'name' : group.name,
                                'id' : group.id,
                                'display_name' : group.display_name,
                                'owner_id' : group.owner_id,
                                'group_type' : group.group_type,
                                'prerequisite_id' : group.prerequisite_id,
                                'creation' : group.creation,
                    }
                    
        return dict(group_list=group_list)
        
        
    @expose("json", allow_json=True)
    def people_list(self, search='*'):
        re_search = re.sub(r'\*', r'%', search).lower()
        people = People.query.filter(People.username.like(re_search)).order_by('username')
        people_list = {}
        for person in people:
            people_list[person.id] = {'id' : person.id,
                                'username' : person.username,
                                'human_name' : person.human_name,
                                'ssh_key' : person.ssh_key,
                                'password' : person.password
                                }
                                

        return dict(people_list=people_list)

