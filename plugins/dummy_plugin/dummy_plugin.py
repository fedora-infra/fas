import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import cherrypy

from genshi.template.plugin import TextTemplateEnginePlugin

class CLA(controllers.Controller):

    def __init__(self):
        '''Create a Dummy Controller.'''

    @expose(template="dummy_plugin.templates.index")
    def index(self):
        return dict()
