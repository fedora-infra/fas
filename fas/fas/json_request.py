import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

from fas.auth import *

class JsonRequest(controllers.Controller):
    def __init__(self):
        '''Create a JsonRequest Controller.'''

    @expose("json")
    def index(self):
        '''Perhaps show a nice explanatory message about groups here?'''
        return dict(help='This is a json interface')

