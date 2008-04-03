# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou All rights reserved.
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
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
#
import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler, config
from cherrypy import session

import cherrypy

from openid.server.server import Server as OpenIDServer
from openid.server.server import BROWSER_REQUEST_MODES
from openid.server.server import OPENID_PREFIX
from openid.store.filestore import FileOpenIDStore

from fas.auth import *

from fas.user import KnownUser

class UserID(validators.Schema):
    targetname = KnownUser

class OpenID(controllers.Controller):

    def __init__(self):
        '''Create a OpenID Controller.'''
        store = FileOpenIDStore(config.get('openidstore'))
        self.openid_server = OpenIDServer(store)#, turbogears.url('/openid/server'))

    @expose()
    def index(self):
        turbogears.redirect('/openid/about')
        return dict()

    @expose(template="fas.templates.openid.about")
    def about(self):
        '''Display an explanatory message about the OpenID service'''
        username = turbogears.identity.current.user_name
        return dict(username=username)

    @expose(template="genshi-text:fas.templates.openid.auth", format="text", content_type='text/plain; charset=utf-8')
    def server(self, **query):
        '''Perform OpenID auth'''
        openid_server = self.openid_server
        openid_query = {}
        openid_request = None
        if not session.has_key('openid_trusted'):
            session['openid_trusted'] = []
        if query.has_key('url') and query.has_key('trusted') and query['trusted'] == 'allow':
            session['openid_trusted'].append(query['url'])
        if query.has_key('openid'):
            try:
                for key in query['openid'].keys():
                    openid_key = OPENID_PREFIX + key
                    openid_query[openid_key] = query['openid'][key]
                openid_request = openid_server.decodeRequest(openid_query)
                session['openid_request'] = openid_request
            except KeyError:
                turbogears.flash(_('The OpenID request could not be decoded.'))
        elif session.has_key('openid_request'):
            openid_request = session['openid_request']
        if openid_request is None:
            turbogears.redirect('/openid/about')
            return dict()
        else:
            openid_response = None
            if openid_request.mode in BROWSER_REQUEST_MODES:
                username = turbogears.identity.current.user_name;
                url = None
                if username is not None:
                    url = config.get('base_url') + turbogears.url('/openid/id/%s' % username)
                if openid_request.identity == url:
                    if openid_request.trust_root in session['openid_trusted']:
                        openid_response = openid_request.answer(True)
                    elif openid_request.immediate:
                        openid_response = openid_request.answer(False, server_url=config.get('base_url') + turbogears.url('/openid/server'))
                    else:
                        if query.has_key('url') and not query.has_key('allow'):
                            openid_response = openid_request.answer(False, server_url=config.get('base_url') + turbogears.url('/openid/server'))
                        else:
                            turbogears.redirect('/openid/trusted', url=openid_request.trust_root)
                elif openid_request.immediate:
                    openid_response = openid_request.answer(False, server_url=config.get('base_url') + turbogears.url('/openid/server'))
                else:
                    turbogears.redirect('/openid/login')
                    return dict()
            else:
                openid_response = openid_server.handleRequest(openid_request)
            web_response = openid_server.encodeResponse(openid_response)
            for name, value in web_response.headers.items():
                cherrypy.response.headers[name] = value;
            cherrypy.response.status = web_response.code
            return dict(body=web_response.body)

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.openid.trusted")
    def trusted(self, url):
        '''Ask the user if they trust a site for OpenID authentication'''
        return dict(url=url)

    @identity.require(turbogears.identity.not_anonymous())
    @expose()
    def login(self):
        '''This exists only to make the user login and then redirect to /openid/server'''
        turbogears.redirect('/openid/server')
        return dict()


    @expose(template="fas.templates.openid.id")
    @validate(validators=UserID())
    def id(self, username):
        '''The "real" OpenID URL'''
        person = People.by_username(username)
        server = config.get('base_url') + turbogears.url('/openid/server')
        return dict(person=person, server=server)

