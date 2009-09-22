#!/usr/bin/python
import sys
sys.path.append('/home/ricky/work/fedora/fas/fas/')
sys.path.append('/home/ricky/work/fedora/fas/')
sys.path.append('/home/ricky/work/fedora/fas/plugins/fas-plugin-asterisk')
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
import fedora.tg.util

class MyNestedVariablesFilter(turbogears.startup.NestedVariablesFilter):
    def before_main(self):
        if hasattr(cherrypy.request, "params"):
            cherrypy.request.params_backup = cherrypy.request.params
        super(MyNestedVariablesFilter, self).before_main()

turbogears.startup.NestedVariablesFilter = MyNestedVariablesFilter

turbogears.update_config(configfile="/home/ricky/work/fedora/fas/fas.cfg", modulename="fas.config")

turbogears.startup.call_on_startup.append(fedora.tg.util.enable_csrf)

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
    # UGH, this is hideous:
    environ['PATH_INFO_OLD'] = environ['PATH_INFO']
    environ['SCRIPT_NAME'] = '/accounts'
    environ['PATH_INFO'] = environ['PATH_INFO'].split('/', 2)[-1]
    req = Request(environ)
    if req.path_info_peek() == '_debug':
        return self.debug(req)(environ, start_response)
    else:
        environ['PATH_INFO'] = environ['PATH_INFO_OLD']
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
