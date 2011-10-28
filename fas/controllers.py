# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou
# Copyright © 2008-2011 Red Hat, Inc.
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
#            Toshio Kuratomi <toshio@redhat.com>
#
from turbogears import expose, config, identity, redirect
from turbogears.database import session
from cherrypy import request

import turbogears
import cherrypy
import time

from fedora.tg import controllers as f_ctrlers
from fedora.tg.utils import request_format

from fas import release
from fas.user import User
from fas.group import Group
from fas.configs import Config
from fas.fpca import FPCA
from fas.json_request import JsonRequest
from fas.help import Help
from fas.model import Session, People
from fas.model import SessionTable

from fas.openid_samadhi import OpenID

from fas.auth import undeprecated_cla_done
from fas.util import available_languages

from fas import plugin

import os

import datetime

try:
    import cPickle as pickle
except ImportError:
    import pickle

class SQLAlchemyStorage:
    def __init__(self):
        pass

    def load(self, session_id):
        s = Session.query.get(session_id)
        if not s:
            return None
        expiration_time = s.expiration_time
        pickled_data = s.data
        data = pickle.loads(pickled_data.encode('utf-8'))
        return (data, expiration_time)

    # This is an iffy one.  CherryPy's built in session
    # storage classes use delete(self, id=None), but it
    # isn't called from anywhere in cherrypy.  I think we
    # can do this as long as we're careful about how we call it.
    def delete(self, session_id=None):
        if session_id is None:
            session_id = cherrypy.session.id
        s = Session.query.get(session_id)
        session.delete(s)
        session.flush()

    def save(self, session_id, data, expiration_time):
        pickled_data = pickle.dumps(data)
        s = Session.query.get(session_id)
        if not s:
            s = Session()
        s.id = session_id
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
        pass
    try:
        return cherrypy.request.simple_cookie['fas_locale'].value
    except KeyError:
        pass

    default_language = config.get('default_language',
            turbogears.i18n.utils._get_locale())
    return default_language

config.update({'i18n.get_locale': get_locale})


def add_custom_stdvars(variables):
    return variables.update({'gettext': _, "lang": get_locale(),
    'available_languages': available_languages(), 
    'fas_version': release.VERSION,
    'webmaster_email': config.get('webmaster_email')})
turbogears.view.variable_providers.append(add_custom_stdvars)

# from fas import json
# import logging
# log = logging.getLogger("fas.controllers")

#TODO: Appropriate flash icons for errors, etc.
# mmcgrath wonders if it will be handy to expose an encrypted mailer with fas
# over json for our apps

class Root(plugin.RootController):

    user = User()
    group = Group()
    fpca = FPCA()
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
            if request_format() == 'json':
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
        (cla_done, undeprecated_cla) = undeprecated_cla_done(person)

        person = person.filter_private()
        return dict(person=person, memberships=person['memberships'], cla=undeprecated_cla)

    @expose(template="fas.templates.about")
    def about(self):
        return dict()

    @expose(template="fas.templates.login", allow_json=True)
    def login(self, forward_url=None, *args, **kwargs):
        '''Page to become authenticated to the Account System.

        This shows a small login box to type in your username and password
        from the Fedora Account System.

        :kwarg forward_url: The url to send to once authentication succeeds
        '''
        login_dict = f_ctrlers.login(forward_url=forward_url, *args, **kwargs)

        if not identity.current.anonymous and identity.was_login_attempted() \
                and not identity.get_identity_errors():
            # Success that needs to be passed back via json
            return login_dict

        if identity.was_login_attempted() and request.fas_provided_username:
            if request.fas_identity_failure_reason == 'status_inactive':
                turbogears.flash(_('Your old password has expired.  Please'
                    ' reset your password below.'))
                if request_format() != 'json':
                    redirect('/user/resetpass')
            if request.fas_identity_failure_reason == 'status_account_disabled':
                turbogears.flash(_('Your account is currently disabled.  For'
                        ' more information, please contact %(admin_email)s' %
                        {'admin_email': config.get('accounts_email')}))
                if request_format() != 'json':
                    redirect('/login')

        return login_dict

    @expose(allow_json=True)
    def logout(self):
        return f_ctrlers.logout()

    @expose()
    def language(self, locale):
        if locale not in available_languages():
            turbogears.flash(_('The language \'%s\' is not available.') % locale)
            redirect(request.headers.get("Referer", "/"))
            return dict()
        #turbogears.i18n.set_session_locale(locale)
        cherrypy.response.simple_cookie['fas_locale'] = locale
        redirect(request.headers.get("Referer", "/"))
        return dict()

