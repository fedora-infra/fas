# -*- coding: utf-8 -*-
#
# Copyright © 2007-2008  Red Hat, Inc. All rights reserved.
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
# Red Hat Author(s): Toshio Kuratomi <tkuratom@redhat.com>
#

'''
This plugin provides integration with the Fedora Account
System using JSON calls.
'''

import Cookie

from cherrypy import request
from sqlalchemy.orm import class_mapper
from turbogears import config, identity
from turbogears.identity.saprovider import SqlAlchemyIdentity, \
        SqlAlchemyIdentityProvider
from turbogears.database import session
from turbogears.util import load_class

# Once this works, propogate the changes back to python-fedora and import as
# from fedora.tg.client import BaseClient
from client import BaseClient

import gettext
t = gettext.translation('python-fedora', '/usr/share/locale', fallback=True)
_ = t.ugettext

import crypt

import logging
log = logging.getLogger('turbogears.identity.safasprovider')

try:
    set, frozenset
except NameError:
    from sets import Set as set, ImmutableSet as frozenset

class JsonFasIdentity(BaseClient):
    '''Associate an identity with a person in the auth system.
    '''
    cookieName = config.get('visit.cookie.name', 'tg-visit')
    fasURL = config.get('fas.url', 'https://admin.fedoraproject.org/admin/fas/')

    def __init__(self, visit_key, user=None, username=None, password=None,
            debug=False):
        super(JsonFasIdentity, self).__init__(self.fasURL, debug=debug)
        if user:
            self._user = user
            self._groups = frozenset(
                    [g['name'] for g in data['person']['approved_memberships']]
                    )
        self.visit_key = visit_key
        # It's allowed to use a null value for a visit_key if we know we're
        # generating an anonymous user.  The json interface doesn't handle
        # that, though, and there's no reason for us to make it.
        if not visit_key:
            return

        # Set the cookie to the user's tg_visit key before requesting
        # authentication.  That way we link the two together.
        self._sessionCookie = Cookie.SimpleCookie()
        self._sessionCookie[self.cookieName] = self.visit_key
        self.username = username
        self.password = password
        if username and password:
            self._authenticate(force=True)

    def _authenticate(self, force=False):
        '''Override BaseClient so we can keep visit_key in sync.
        '''
        super(JsonFasIdentity, self)._authenticate(force)
        if self._sessionCookie[self.cookieName].value != self.visit_key:
            # When the visit_key changes (because the old key had expired or
            # been deleted from the db) change the visit_key in our variables
            # and the session cookie to be sent back to the client.
            self.visit_key = self._sessionCookie[self.cookieName].value
            cookies = request.simple_cookie
            cookies[self.cookieName] = self.visit_key
        return self._sessionCookie
    session = property(_authenticate)

    def _get_user(self):
        '''Retrieve information about the user from cache or network.'''
        try:
            return self._user
        except AttributeError:
            # User hasn't already been set
            pass
        # Attempt to load the user. After this code executes, there *WILL* be
        # a _user attribute, even if the value is None.
        # Query the account system URL for our given user's sessionCookie
        # FAS returns user and group listing
        data = self.send_request('user/view', auth=True)
        if not data['person']:
            self._user = None
            return None
        self._user = data['person']
        self._groups = frozenset(
                [g['name'] for g in data['person']['approved_memberships']]
                )
        return self._user
    user = property(_get_user)

    def _get_user_name(self):
        if not self.user:
            return None
        return self.user['username']
    user_name = property(_get_user_name)

    def _get_groups(self):
        try:
            return self._groups
        except AttributeError:
            # User and groups haven't been returned.  Since the json call
            # returns both user and groups, this is set at user creation time.
            self._groups = frozenset()
        return self._groups
    groups = property(_get_groups)

    def logout(self):
        '''
        Remove the link between this identity and the visit.
        '''
        if not self.visit_key:
            return
        # Call Account System Server logout method
        self.send_request('logout', auth=True)

class JsonFasIdentityProvider(object):
    '''
    IdentityProvider that authenticates users against the fedora account system
    '''
    def __init__(self):
        # Default encryption algorithm is to use plain text passwords
        algorithm = config.get("identity.saprovider.encryption_algorithm", None)
        self.encrypt_password = lambda pw: \
                                    identity._encrypt_password(algorithm, pw)

    def create_provider_model(self):
        '''
        Create the database tables if they don't already exist.
        '''
        # No database tables to create because the db is behind the FAS2
        # server
        pass

    def validate_identity(self, user_name, password, visit_key):
        '''
        Look up the identity represented by user_name and determine whether the
        password is correct.

        Must return either None if the credentials weren't valid or an object
        with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''
        try:
            user = JsonFasIdentity(visit_key, username=user_name,
                    password=password)
        except AuthError, e:
            log.warning('Error logging in %(user)s: %(error)s' % {
                'user': username, 'error': e})
            return None

        return JsonFasIdentity(visit_key, user)

    def validate_password(self, user, user_name, password):
        '''
        Check the supplied user_name and password against existing credentials.
        Note: user_name is not used here, but is required by external
        password validation schemes that might override this method.
        If you use SqlAlchemyIdentityProvider, but want to check the passwords
        against an external source (i.e. PAM, LDAP, Windows domain, etc),
        subclass SqlAlchemyIdentityProvider, and override this method.

        Arguments:
        :user: User information.  Not used.
        :user_name: Given username.
        :password: Given, plaintext password.

        Returns: True if the password matches the username.  Otherwise False.
          Can return False for problems within the Account System as well.
        '''
        
        return user.password == crypt.crypt(password, user.password)

    def load_identity(self, visit_key):
        '''Lookup the principal represented by visit_key.

        Arguments:
        :visit_key: The session key for whom we're looking up an identity.

        Must return an object with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''
        return JsonFasIdentity(visit_key)

    def anonymous_identity(self):
        '''
        Must return an object with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''

        return JsonFasIdentity(None)

    def authenticated_identity(self, user):
        '''
        Constructs Identity object for user that has no associated visit_key.
        '''
        return JsonFasIdentity(None, user)
