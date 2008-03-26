# -*- coding: utf-8 -*-
import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import cherrypy

from genshi.template.plugin import TextTemplateEnginePlugin

class DummyPlugin(controllers.Controller):
    capabilities = ['dummy_plugin']

    def __init__(self):
        '''Create a Dummy Controller.'''

    @expose(template="fas_dummy.templates.index")
    def index(self):
        value = "my Val"
        return dict(value=value)
