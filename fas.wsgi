#!/usr/bin/python
import __main__
if not hasattr(__main__, '__requires__'):
    __main__.__requires__ = []
__main__.__requires__.append('SQLAlchemy >= 0.5, <= 0.6')
__main__.__requires__.append('TurboGears[future]')

import sys
sys.stdout = sys.stderr

import pkg_resources
pkg_resources.require('CherryPy <= 3.0alpha')
pkg_resources.require('SQLAlchemy')

import os
os.environ['PYTHON_EGG_CACHE'] = '/var/www/.python-eggs'

import atexit
import cherrypy
import cherrypy._cpwsgi
import turbogears
import turbogears.startup
import fedora.tg.utils

class MyNestedVariablesFilter(turbogears.startup.NestedVariablesFilter):
    def before_main(self):
        if hasattr(cherrypy.request, "params"):
            cherrypy.request.params_backup = cherrypy.request.params
        super(MyNestedVariablesFilter, self).before_main()

turbogears.startup.NestedVariablesFilter = MyNestedVariablesFilter

turbogears.update_config(configfile="/etc/fas.cfg", modulename="fas.config")
turbogears.config.update({'global': {'autoreload.on': False}})

turbogears.startup.call_on_startup.append(fedora.tg.utils.enable_csrf)

import fas.controllers

cherrypy.root = fas.controllers.Root()

# Uncomment this (and the below section) to use weberror for development
#from weberror.evalexception import EvalException

if cherrypy.server.state == 0:
    atexit.register(cherrypy.server.stop)
    cherrypy.server.start(init_only=True, server_class=None)

from webob import Request

def application(environ, start_response):
    environ['SCRIPT_NAME'] = ''
    return cherrypy._cpwsgi.wsgiApp(environ, start_response)

def fake_call(self, environ, start_response):
    ## FIXME: print better error message (maybe fall back on
    ## normal middleware, plus an error message)
    assert not environ['wsgi.multiprocess'], (
        "The EvalException middleware is not usable in a "
        "multi-process environment")
    # XXX: Legacy support for Paste restorer
    environ['weberror.evalexception'] = environ['paste.evalexception'] = \
        self

    environ['SCRIPT_NAME'] = '/accounts'
    req = Request(environ)

    # PATCH: Remove the /accounts component
    if req.path_info.lstrip('/').split('/')[1] == '_debug':
        req.path_info_pop()
        return self.debug(req)(environ, start_response)
    else:
        return self.respond(environ, start_response)

# Uncomment these lines (and the above weberror import) to use weberror
# for testing.  This requires that python-weberror and its dependencies
# are installed.  debug must be set on above, and mod_wsgi must only use
# one process (don't specify processes= in the WSGIDaemonProcess directive.
# Due to a current WebError bug
# (http://bitbucket.org/bbangert/weberror/issue/2/reliance-on-side-effect-of-an-assert)
# WSGIPythonOptimize must be 0 for this to work properly.
#setattr(EvalException, '__call__', fake_call)
#application = EvalException(application, global_conf={'debug': True})
