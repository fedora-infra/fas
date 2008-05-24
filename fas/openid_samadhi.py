# -*- coding: utf-8 -*-

# Copyright 2008 by Jeffrey C. Ollie
#
# This file is part of Samadhi.
#
# Samadhi is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License.
#
# Samadhi is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Samadhi.  If not, see <http://www.gnu.org/licenses/>.

from turbogears import controllers, expose, flash
from fas import model

from turbogears import identity, redirect, config
from turbogears import url as tg_url

from cherrypy import request, response, session

# from samadhi import json
import logging
log = logging.getLogger("samadhi.controllers")

import openid

from openid.extensions import sreg
from openid.server import server
from openid.consumer import discover

from urlparse import urljoin

def build_url(newpath):
    base_url = config.get('samadhi.baseurl')
    return urljoin(base_url, tg_url(newpath))

login_url = build_url('/login')
id_base_url = build_url('/openid/id')
endpoint_url = build_url('/openid/server')
yadis_base_url = build_url('/openid/yadis')

class OpenID(controllers.Controller):
    def __init__(self, *args, **kw):
        super(OpenID, self).__init__(*args, **kw)
        store = model.SamadhiStore()
        self.openid = server.Server(store, endpoint_url)

    @expose(template="fas.templates.openid.welcome")
    def index(self):
        return dict(login_url = login_url, id_base_url = id_base_url)

    @expose(template="fas.templates.openid.id")
    def id(self, *args, **kw):
        results = dict(endpoint_url = endpoint_url,
                       yadis_url = build_url(yadis_base_url + '/' + '/'.join(args)),
                       user_url = None)
            
        if len(args) >= 1:
            results['user_url'] = build_url(id_base_url + '/' + '/'.join(args)),

        return results

    @expose(template="fas.templates.openid.yadis", format="xml", content_type="application/xrds+xml")
    def yadis(self, *args, **kw):
        results = dict(discover = discover,
                       endpoint_url = endpoint_url,
                       yadis_url = build_url(yadis_base_url + '/' + '/'.join(args)),
                       user_url = None)

        if len(args) >= 1:
            results['user_url'] = build_url(id_base_url + '/' + '/'.join(args)),
        return results

    @expose()
    def server(self, *args, **kw):
        try:
            openid_request = self.openid.decodeRequest(request.params_backup)
        except server.ProtocolError, openid_error:
            return self.respond(openid_error)

        if openid_request is None:
            return dict(tg_template = "fas.templates.openid.about",
                        endpoint_url = endpoint_url)

        elif openid_request.mode in ["checkid_immediate", "checkid_setup"]:
            return self.checkidrequest(openid_request)

        else:
            return self.respond(self.openid.handleRequest(openid_request))

    def isauthorized(self, openid_identity, openid_trust_root):
        if identity.current.anonymous:
            return False

        if build_url(id_base_url + '/' + identity.current.user_name) != openid_identity:
            return False

        key = (openid_identity, openid_trust_root)

        return session.get(key)

    def checkidrequest(self, openid_request):
        isauthorized = self.isauthorized(openid_request.identity, openid_request.trust_root)

        if identity.current.anonymous:
            return redirect('/openid/login', url=request.browser_url)

        elif isauthorized == False:
            return self.respond(openid_request.answer(False))

        elif isauthorized == 'always':
            return self.respond(openid_request.answer(True))

        elif openid_request.immediate or isauthorized == 'never':
            return self.respond(openid_request.answer(False))

        else:
            session.acquire_lock()
            session['last_request'] = openid_request
            return self.showdecidepage(openid_request)

    def showdecidepage(self, openid_request):
        sreg_req = sreg.SRegRequest.fromOpenIDRequest(openid_request)

        return dict(tg_template='fas.templates.openid.authorizesite',
                    identity = openid_request.identity,
                    trust_root = openid_request.trust_root,
                    sreg_req = sreg_req,
                    data_fields = sreg.data_fields)

    def respond(self, openid_response):
        try:
            webresponse = self.openid.encodeResponse(openid_response)
            response.status = webresponse.code
            response.headers.update(webresponse.headers)
            
            if webresponse.body:
                return webresponse.body
            return ''

        except server.EncodingError, why:
            text = why.response.encodeToKVForm()
            response.status = 400
            response.headers['Content-type'] = 'text/plain; charset=UTF-8'
            return text
        
    @expose()
    def allow(self, *args, **kw):
        openid_request = session.get('last_request')

        # TODO: check to make sure that request was found in session
        remember_value = ''

        if 'yes' in kw:
            openid_response = openid_request.answer(True)
            remember_value = 'always'
            sreg_req = sreg.SRegRequest.fromOpenIDRequest(openid_request)
            fields = sreg_req.allRequestedFields()
            values = {}
            if 'sreg' in kw and 'send' in kw['sreg']:
                values = {
                    'nickname': identity.current.user.username,
                    'email': identity.current.user.email,
                    'fullname': identity.current.user.human_name,
                    'timezone': identity.current.user.timezone,
                    }
                for field in values.keys():
                    if kw['sreg']['send'][field] != 'yes':
                        del(values[field])
            sreg_resp = sreg.SRegResponse.extractResponse(sreg_req, values)
            sreg_resp.toMessage(openid_response.fields)
        
        elif 'no' in kw:
            openid_response = openid_request.answer(False)
            remember_value = 'never'

        else:
            assert False, 'strange allow post %s' % kw

        if kw.get('remember', 'no') == 'yes':
            session.acquire_lock()
            session[(openid_request.identity, openid_request.trust_root)] = remember_value

        return self.respond(openid_response)

    @expose()
    @identity.require(identity.not_anonymous())
    def login(self, url):
        """Force the user to login, while preserving the originating URL"""
        redirect(url)
