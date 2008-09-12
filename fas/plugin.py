# -*- coding: utf-8 -*-
#
# Copyright © 2008 Ignacio Vazquez-Abrams All rights reserved.
# Copyright © 2008 Red Hat, Inc. All rights reserved.
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
# Author(s): Ignacio Vazquez-Abrams <ivazquez@fedoraproject.org>
#

import turbogears.controllers as controllers
import turbogears.startup as startup
import pkg_resources

class BadPathException(Exception):
    pass

class PathUnavailableException(Exception):
    pass

class PluginControllerMixin(object):
    def requestpath(controller, plugin, path):
        '''Used by a plugin to request addition to a path'''
        if isinstance(path, basestring):
            path = path.split('/')
            if len(path) > 0 and len(path[0]) == 0:
                del path[0]
        if len(path) == 0:
            raise BadPathException('Empty path specified')
        frag = getattr(controller, path[0], None)
        if frag is None:
            p = plugin()
            p._root = controller
            setattr(controller, path[0], p)
            controller.plugins.append(p)
            return '/' + path[0] + '/', p
        if hasattr(frag, 'requestpath'):
            if len(path) > 1:
                return '/' + path[0] + frag.requestpath(plugin, path[1:])
            raise PathUnavailableException('Path not deep enough')
        raise PathUnavailableException('Path already in use')

    def getpluginident(controller):
        '''The string returned by this method is prepended to ".plugins"
        in order to search for plugins'''
        raise NotImplementedError('Whoops! Forgot to override getpluginident!')

    def loadplugins(controller):
        for pluginEntry in pkg_resources.iter_entry_points('%s.plugins' %
            controller.getpluginident()): 
            pluginClass = pluginEntry.load() 
            if hasattr(pluginClass, 'initPlugin'): 
                pluginClass.initPlugin(controller)
        startup.call_on_shutdown.append(controller.unloadplugins)

    def unloadplugins(controller):
        for plugin in controller.plugins:
            if hasattr(plugin, 'delPlugin'):
                plugin.delPlugin(controller)

class RootController(controllers.RootController, PluginControllerMixin):
    def __init__(self, *args, **kwargs):
        super(controllers.RootController, self).__init__(*args, **kwargs)
        PluginControllerMixin.__init__(self, *args, **kwargs)
        self.plugins = []
        self.loadplugins()
    

class Controller(controllers.Controller, PluginControllerMixin):
    def __init__(self, *args, **kwargs):
        super(controllers.Controller, self).__init__(*args, **kwargs)
        self.plugins = []
        self.loadplugins()

__all__ = [PluginControllerMixin, RootController, Controller,
    BadPathException, PathUnavailableException]
