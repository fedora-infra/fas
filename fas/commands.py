# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou
# Copyright © 2011 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
#
"""This module contains functions called from console script entry points."""

import os
import sys

import pkg_resources
pkg_resources.require("TurboGears")

import turbogears
import cherrypy
import fedora.tg.utils

cherrypy.lowercase_api = True

class ConfigurationError(Exception):
    pass

import turbogears.startup

class MyNestedVariablesFilter(turbogears.startup.NestedVariablesFilter):
    def before_main(self):
        if hasattr(cherrypy.request, "params"):
            cherrypy.request.params_backup = cherrypy.request.params
        super(MyNestedVariablesFilter, self).before_main()

turbogears.startup.NestedVariablesFilter = MyNestedVariablesFilter

def start():
    '''Start the CherryPy application server.'''
    turbogears.startup.call_on_startup.append(fedora.tg.utils.enable_csrf)
    setupdir = os.path.dirname(os.path.dirname(__file__))
    curdir = os.getcwd()

    # First look on the command line for a desired config file,
    # if it's not on the command line, then look for 'setup.py'
    # in the current directory. If there, load configuration
    # from a file called 'dev.cfg'. If it's not there, the project
    # is probably installed and we'll look first for a file called
    # 'prod.cfg' in the current directory and then for a default
    # config file called 'default.cfg' packaged in the egg.
    if len(sys.argv) > 1:
        configfile = sys.argv[1]
    elif os.path.exists(os.path.join(setupdir, 'setup.py')) \
            and os.path.exists(os.path.join(setupdir, 'dev.cfg')):
        configfile = os.path.join(setupdir, 'dev.cfg')
    elif os.path.exists(os.path.join(curdir, 'fas.cfg')):
        configfile = os.path.join(curdir, 'fas.cfg')
    elif os.path.exists(os.path.join('/etc/fas.cfg')):
        configfile = os.path.join('/etc/fas.cfg')
    else:
        try:
            configfile = pkg_resources.resource_filename(
              pkg_resources.Requirement.parse("fas"),
                "config/default.cfg")
        except pkg_resources.DistributionNotFound:
            raise ConfigurationError("Could not find default configuration.")

    turbogears.update_config(configfile=configfile,
        modulename="fas.config")

    from fas.controllers import Root
    turbogears.start_server(Root())
