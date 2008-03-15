from turbogears import controllers, expose, config
from model import *
from turbogears import identity, redirect, widgets, validate, validators, error_handler
from cherrypy import request, response

from turbogears import exception_handler
import turbogears
import cherrypy
import time

from fas.user import User
from fas.group import Group
from fas.cla import CLA
from fas.json_request import JsonRequest
from fas.help import Help
from fas.auth import *
#from fas.openid_fas import OpenID

import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def add_custom_stdvars(vars):
    return vars.update({"gettext": _})

turbogears.view.variable_providers.append(add_custom_stdvars)

def get_locale(locale=None):
    if locale:
        return locale
    try:
        return turbogears.identity.current.user.locale
    except AttributeError:
        return turbogears.i18n.utils._get_locale()

config.update({'i18n.get_locale': get_locale})

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
    help = Help()
    #openid = OpenID()

    # TODO: Find a better place for this.
    os.environ['GNUPGHOME'] = config.get('gpghome')

    @expose(template="fas.templates.welcome", allow_json=True)
    def index(self):
        if turbogears.identity.not_anonymous():
            if 'tg_format' in request.params \
                    and request.params['tg_format'] == 'json':
                # redirects don't work with JSON calls.  This is a bit of a
                # hack until we can figure out something better.
                return dict()
            turbogears.redirect('/home')
        return dict(now=time.ctime())

    @expose(template="fas.templates.home", allow_json=True)
    @identity.require(identity.not_anonymous())
    def home(self):
        user_name = turbogears.identity.current.user_name
        person = People.by_username(user_name)
        cla = CLADone(person)
        return dict(person=person, cla=cla)

    @expose(template="fas.templates.about")
    def about(self):
        return dict()

    @expose(template="fas.templates.login", allow_json=True)
    def login(self, forward_url=None, previous_url=None, *args, **kwargs):
        '''Page to become authenticated to the Account System.

        This shows a small login box to type in your username and password
        from the Fedora Account System.
        
        Arguments:
        :forward_url: The url to send to once authentication succeeds
        :previous_url: The url that sent us to the login page
        '''
        if forward_url == '.':
            forward_url = turbogears.url('/../home')
        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            # User is logged in
            turbogears.flash(_('Welcome, %s') % People.by_username(turbogears.identity.current.user_name).human_name)
            if 'tg_format' in request.params \
                    and request.params['tg_format'] == 'json':
                # When called as a json method, doesn't make any sense to
                # redirect to a page.  Returning the logged in identity
                # is better.
                return dict(user = identity.current.user)
            if not forward_url:
                forward_url = turbogears.url('/')
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
            forward_url= '.'

        cherrypy.response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=request.params,
                    forward_url=forward_url)

    @expose(allow_json=True)
    def logout(self):
        identity.current.logout()
        turbogears.flash(_('You have successfully logged out.'))
        if 'tg_format' in request.params \
                and request.params['tg_format'] == 'json':
            # When called as a json method, doesn't make any sense to
            # redirect to a page.  Returning the logged in identity
            # is better.
            return dict(status=True)
        raise redirect('/')

    @expose()
    def language(self, locale):
        locale_key = config.get("i18n.session_key", "locale")
        cherrypy.session[locale_key] = locale
        raise redirect(request.headers.get("Referer", "/"))


