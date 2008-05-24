#!/usr/bin/python
import sys
sys.path.append('/home/ricky/work/fedora/fas/fas/')
sys.path.append('/home/ricky/work/fedora/fas/')
sys.stdout = sys.stderr

import pkg_resources
pkg_resources.require('CherryPy <= 3.0alpha')

import os
os.environ['PYTHON_EGG_CACHE'] = '/home/ricky/work/fedora/fas/fas.egg-info/'

import atexit
import cherrypy
import cherrypy._cpwsgi
import turbogears
import turbogears.startup

class MyNestedVariablesFilter(turbogears.startup.NestedVariablesFilter):
    def before_main(self):
        if hasattr(cherrypy.request, "params"):
            cherrypy.request.params_backup = cherrypy.request.params
        super(MyNestedVariablesFilter, self).before_main()

turbogears.startup.NestedVariablesFilter = MyNestedVariablesFilter

turbogears.update_config(configfile="/home/ricky/work/fedora/fas/fas.cfg", modulename="fas.config")
turbogears.config.update({'global': {'server.environment': 'development'}})
turbogears.config.update({'global': {'autoreload.on': False}})
turbogears.config.update({'global': {'server.log_to_screen': False}})
turbogears.config.update({'global': {'server.webpath': '/accounts'}})
turbogears.config.update({'global': {'base_url_filter.on': True}})
turbogears.config.update({'global': {'base_url_filter.base_url': 'http://admin.fedora.riczho.dyndns.org'}})

import fas.controllers

cherrypy.root = fas.controllers.Root()

if cherrypy.server.state == 0:
    atexit.register(cherrypy.server.stop)
    cherrypy.server.start(init_only=True, server_class=None)

def application(environ, start_response):
    environ['SCRIPT_NAME'] = ''
    return cherrypy._cpwsgi.wsgiApp(environ, start_response)
