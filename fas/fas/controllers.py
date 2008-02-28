from turbogears import controllers, expose, config
from model import *
from turbogears import identity, redirect, widgets, validate, validators, error_handler
from cherrypy import request, response

from turbogears import exception_handler
import turbogears
import time

from fas.user import User
from fas.group import Group
from fas.cla import CLA
from fas.json_request import JsonRequest
#from fas.openid_fas import OpenID

import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def add_custom_stdvars(vars):
    return vars.update({"gettext": _})

turbogears.view.variable_providers.append(add_custom_stdvars)

# from fas import json
# import logging
# log = logging.getLogger("fas.controllers")

#TODO: Appropriate flash icons for errors, etc.
# mmcgrath wonders if it will be handy to expose an encrypted mailer with fas over json for our apps

class Root(controllers.RootController):

    user = User()
    group = Group()
    cla = CLA()
    json = JsonRequest()
#    openid = OpenID()

    # TODO: Find a better place for this.
    os.environ['GNUPGHOME'] = config.get('gpghome')

    @expose(template="fas.templates.welcome", allow_json=True)
    def index(self):
        if turbogears.identity.not_anonymous():
            turbogears.redirect('/home')
        return dict(now=time.ctime())

    @expose(template="fas.templates.home")
    @identity.require(identity.not_anonymous())
    def home(self):
        return dict()

    @expose(template="fas.templates.login")
    def login(self, forward_url=None, previous_url=None, *args, **kw):

        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            turbogears.flash(_('Welcome, %s') % People.by_username(turbogears.identity.current.user_name).human_name)
            if not forward_url:
                forward_url = config.get('base_url_filter.base_url') + '/'
            raise redirect(forward_url)

        forward_url=None
        previous_url= request.path

        if identity.was_login_attempted():
            msg=_("The credentials you supplied were not correct or "
                   "did not grant access to this resource.")
        elif identity.get_identity_errors():
            msg=_("You must provide your credentials before accessing "
                   "this resource.")
        else:
            msg=_("Please log in.")
            forward_url= request.headers.get("Referer", "/")

        response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=request.params,
                    forward_url=forward_url)

    @expose()
    def logout(self):
        identity.current.logout()
        turbogears.flash(_('You have successfully logged out.'))
        raise redirect(request.headers.get("Referer", "/"))
