import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler, config
from cherrypy import session

import ldap
import cherrypy
import fas.fasLDAP

from openid.server.server import Server as OpenIDServer
from openid.server.server import BROWSER_REQUEST_MODES
from openid.server.server import OPENID_PREFIX
from openid.store.filestore import FileOpenIDStore

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

from fas.auth import *

from fas.user import knownUser, userNameExists

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
        userName = turbogears.identity.current.user_name
        return dict(userName=userName)

    @expose(template="genshi-text:fas.templates.openid.auth", format="text", content_type='text/plain; charset=utf-8')
    def server(self, **query):
        '''Perform OpenID auth'''
        openid_server = self.openid_server
        openid_query = {}
        openid_request = None
        if query.has_key('openid'):
            try:
                for key in query['openid'].keys():
                    openid_key = OPENID_PREFIX + key
                    openid_query[openid_key] = query['openid'][key]
                openid_request = openid_server.decodeRequest(openid_query)
            except KeyError:
                turbogears.flash(_('The OpenID request could not be decoded.'))
        elif session.has_key('openid_request'):
            openid_request = session['openid_request']
        if openid_request is None:
            turbogears.redirect('/openid/about')
            return dict()
        else:
            openid_response = None
            session['openid_request'] = openid_request
            if openid_request.mode in BROWSER_REQUEST_MODES:
                userName = turbogears.identity.current.user_name;
                url = None
                if userName is not None:
                    url = config.get('base_url') + turbogears.url('/openid/id/%s' % userName)
                if openid_request.identity == url:
                    # TODO: Check openid_request.trust_root
                    openid_response = openid_request.answer(True)
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
    @expose()
    def login(self):
        '''This exists only to make the user login and then redirect to /openid/server'''
        userName = turbogears.identity.current.user_name;
        turbogears.redirect('/openid/server')
        return dict()


    @expose(template="fas.templates.openid.id")
    @validate(validators=userNameExists())
    def id(self, userName):
        '''The "real" OpenID URL'''
        user = Person.byUserName(userName)
        server = config.get('base_url') + turbogears.url('/openid/server')
        return dict(user=user, server=server)

