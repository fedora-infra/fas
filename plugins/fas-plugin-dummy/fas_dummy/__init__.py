# -*- coding: utf-8 -*-
import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import cherrypy

from genshi.template.plugin import TextTemplateEnginePlugin

import fas.sidebar as sidebar
import logging
import fas.plugin as plugin

class DummyPlugin(controllers.Controller):
    capabilities = ['dummy_plugin']

    def __init__(self):
        '''Create a Dummy Controller.'''
        self.path = ''

    @expose(template="fas_dummy.templates.index")
    def index(self):
        value = "my Val"
        return dict(value=value)

    @classmethod
    def initPlugin(cls, controller):
        cls.log = logging.getLogger('plugin.dummy')
        cls.log.info('Dummy plugin initializing')
        try:
            path, self = controller.requestpath(cls, '/dummy')
            cls.log.info('Dummy plugin hooked')
            self.path = path
            if self.sidebarentries not in sidebar.entryfuncs:
                sidebar.entryfuncs.append(self.sidebarentries)
        except (plugin.BadPathException,
            plugin.PathUnavailableException), e:
            cls.log.info('Dummy plugin hook failure: %s' % e)

    def delPlugin(self, controller):
        self.log.info('Dummy plugin shutting down')
        if self.sidebarentries in sidebar.entryfuncs:
            sidebar.entryfuncs.remove(self.sidebarentries)
            
    def sidebarentries(self):
        return [('Dummy plugin', self.path)]
