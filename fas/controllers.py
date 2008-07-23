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
from turbogears import expose, config, identity, redirect
from turbogears.database import session
from cherrypy import request

import turbogears
import cherrypy
import time

from fas import release
from fas.user import User
from fas.group import Group
from fas.configs import Config
from fas.cla import CLA
from fas.json_request import JsonRequest
from fas.help import Help
from fas.model import Session, People
from fas.model import SessionTable

from fas.openid_samadhi import OpenID

from fas.auth import CLADone
from fas.util import available_languages

from fas import plugin

import os

import datetime

try:
      import cPickle as pickle
except ImportError:
      import pickle

### FIXME: If cherrypy isn't using keyword args to call these methods, we should
# rename from id => sessionid as id is a builtin.
class SQLAlchemyStorage:
    def __init__(self):
        pass

    def load(self, id):
        s = Session.query.get(id)
        if not s:
            return None
        expiration_time = s.expiration_time
        pickled_data = s.data
        data = pickle.loads(pickled_data.encode('utf-8'))
        return (data, expiration_time)

    def delete(self, id=None):
        if id is None:
            id = cherrypy.session.id
        s = Session.query.get(id)
        session.delete(s)
        session.flush()

    def save(self, id, data, expiration_time):
        pickled_data = pickle.dumps(data)
        s = Session.query.get(id)
        if not s:
            s = Session()
        s.id = id
        s.data = pickled_data
        s.expiration_time = expiration_time
        session.flush()

    def acquire_lock(self):
        pass

    def release_lock(self):
        pass

    def clean_up(self, sess):
        result = SessionTable.delete(
            SessionTable.c.expiration_time.__lt__(datetime.datetime.now())
            ).execute()

config.update({'session_filter.storage_class': SQLAlchemyStorage})

def get_locale(locale=None):
    if locale:
        return locale
    try:
        return turbogears.identity.current.user.locale
    except AttributeError:
        return turbogears.i18n.utils._get_locale()

config.update({'i18n.get_locale': get_locale})


def add_custom_stdvars(variables):
  return variables.update({'gettext': _, "lang": get_locale(), 'available_languages': available_languages(), 'fas_version': release.VERSION})
turbogears.view.variable_providers.append(add_custom_stdvars)

# from fas import json
# import logging
# log = logging.getLogger("fas.controllers")

#TODO: Appropriate flash icons for errors, etc.
# mmcgrath wonders if it will be handy to expose an encrypted mailer with fas over json for our apps

class Root(plugin.RootController):

    user = User()
    group = Group()
    cla = CLA()
    json = JsonRequest()
    config = Config()
    help = Help()

    openid = OpenID()

    def __init__(self):
        # TODO: Find a better place for this.
        os.environ['GNUPGHOME'] = config.get('gpghome')
        plugin.RootController.__init__(self)

    def getpluginident(self):
        return 'fas'

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

    @identity.require(identity.not_anonymous())
    @expose(template="fas.templates.home", allow_json=True)
    def home(self):
        user_name = turbogears.identity.current.user_name
        person = People.by_username(user_name)
        cla = CLADone(person)
        person = person.filter_private()
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
                return dict(user=identity.current.user)
            if not forward_url:
                forward_url = turbogears.url('/')
            raise redirect(forward_url)

        forward_url=None
        previous_url= request.path

        if identity.was_login_attempted() and request.fas_provided_username:
            print 'FIXME: Do something with this:', request.fas_identity_failure_reason
            pass

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
        if locale not in available_languages():
            turbogears.flash(_('The language \'%s\' is not available.') % locale)
            redirect(request.headers.get("Referer", "/"))
            return dict()
        turbogears.i18n.set_session_locale(locale)
        redirect(request.headers.get("Referer", "/"))
        return dict()

