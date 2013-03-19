# -*- coding: utf-8 -*-
#
# Copyright © 2007-2008  Red Hat, Inc.
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
# Author(s): Toshio Kuratomi <tkuratom@redhat.com>
#            Ricky Zhou <ricky@fedoraproject.org>
# Adapted from code in the TurboGears project licensed under the MIT license.

'''
This plugin provides authentication of passwords against the Fedora Account
System.
'''

import crypt
try:
    from hashlib import sha1 as hash_constructor
except ImportError:
    from sha import new as hash_constructor

from sqlalchemy.orm import class_mapper
from turbogears import config, identity, flash
from turbogears.database import session
from turbogears.util import load_class
from turbogears.identity import set_login_attempted

from fas.model import People, Configs

import pytz
from datetime import datetime

import sys, os, re
import urllib2

import cherrypy

import gettext
t = gettext.translation('fas', '/usr/share/locale', fallback=True)
_ = t.ugettext

import logging
log = logging.getLogger('turbogears.identity.safasprovider')

try:
    set, frozenset
except NameError:
    # :W0622: We need a set type on earlier pythons.
    from sets import Set as set # pylint: disable-msg=W0622
    from sets import ImmutableSet as frozenset # pylint: disable-msg=W0622

# Global class references --
# these will be set when the provider is initialised.
user_class = None
visit_class = None

def get_configs(configs_list):
    configs = {}
    for config in configs_list:
        configs[config.attribute] = config.value
    if 'enabled' not in configs:
        configs['enabled'] = '0'
    if 'prefix' not in configs:
        configs['prefix'] = 'Not Defined'
    return configs

def otp_check(key):
    '''Check otp key string'''
    if config.get('yubi_enabled', False) and config.get('yubi_server_prefix', False):
        if len(key) == 44 and key.startswith('ccccc'):
            log.debug('OTP key matches criteria.')
            return True

    log.debug('OTP key check failed!')
    return False

def otp_validate(user_name, otp):
    '''
    Check supplied otp key and username against existing credentials

    :arg user_name: User login
    :arg otp: Given OTP key
    :returns: True if given args match from OTP provider
    '''
    client_id = '1'

    target = People.by_username(user_name)
    configs = get_configs(Configs.query.filter_by(person_id=target.id, application='yubikey').all())

    if not otp.startswith(configs['prefix']):
      return False

    server_prefix = config.get('yubi_server_prefix', 'http://localhost/yk-val/verify?id=')
    auth_regex = re.compile('^status=(?P<rc>\w{2})')

    server_url = server_prefix + client_id + "&otp=" + otp

    fh = urllib2.urlopen(server_url)

    for line in fh:
        match = auth_regex.search(line.strip('\n'))
        if match:
            if match.group('rc') == 'OK':
                return True
        else:
            return False
        break

    return False

class SaFasIdentity(object):
    '''Identity that uses a model from a database (via SQLAlchemy).'''

    def __init__(self, visit_key=None, user=None, using_ssl=False):
        self.visit_key = visit_key
        self._visit_link = None
        if user:
            self._user = user
            if visit_key is not None:
                self.login(using_ssl)

    def __retrieve_user(self, visit):
        '''Attempt to load the user from the visit_key.

        :returns: a user or None
        '''
        # I hope this is a safe place to double-check the SSL variables.
        # TODO: Double check my logic with this - is it unnecessary to
        # check that the username matches up?
        if visit.ssl and cherrypy.request.headers['X-Client-Verify'] != 'SUCCESS':
            self.logout()
            return None

        user = user_class.query.get(visit.user_id)

        # This is a hack, need to talk to Toshio abvout it.w
        user.approved_memberships

        if user.status in ('inactive', 'expired', 'admin_disabled'):
            log.warning("User %(username)s has status %(status)s, logging them out." % \
                { 'username': user.username, 'status': user.status })
            self.logout()
            user = None
        return user

    def _get_user(self):
        '''Get user instance for this identity.'''
        visit = self.visit_link
        if not visit:
            self._user = None
        else:
            if (not '_csrf_token' in cherrypy.request.params or
                    cherrypy.request.params['_csrf_token'] !=
                    hash_constructor(self.visit_key).hexdigest()):
                log.info("Bad _csrf_token")
                if '_csrf_token' in cherrypy.request.params:
                    log.info("visit: %s token: %s" % (self.visit_key,
                        cherrypy.request.params['_csrf_token']))
                else:
                    log.info('No _csrf_token present')
                cherrypy.request.fas_identity_failure_reason = 'bad_csrf'
                self._user = None

            try:
                return self._user
            except AttributeError:
                # User hasn't already been set
                # Attempt to load the user. After this code executes, there
                # *will* be a _user attribute, even if the value is None.
                self._user = self.__retrieve_user(visit)
        return self._user
    user = property(_get_user)

    def _get_token(self):
        if self.visit_key:
            return hash_constructor(self.visit_key).hexdigest()
        else:
            return ''
    csrf_token = property(_get_token)

    def _get_user_name(self):
        '''Get user name of this identity.'''
        if not self.user:
            return None
        ### TG: Difference: Different name for the field
        return self.user.username
    user_name = property(_get_user_name)

    ### TG: Same as TG-1.0.8
    def _get_user_id(self):
        '''Get user id of this identity.'''
        if not self.user:
            return None
        return self.user.user_id
    user_id = property(_get_user_id)

    ### TG: Same as TG-1.0.8
    def _get_anonymous(self):
        '''Return true if not logged in.'''
        return not self.user
    anonymous = property(_get_anonymous)

    def _get_only_token(self):
        '''
        In one specific instance in the login template we need to know whether
        an anonymous user is just lacking a token.
        '''
        visit = self.visit_link
        if visit and self.__retrieve_user(visit):
            # user is valid, just the token is missing
            return True

        # Else the user still has to login
        return False
    only_token = property(_get_only_token)

    def _get_permissions(self):
        '''Get set of permission names of this identity.'''
        ### TG difference: No permissions in FAS
        return frozenset()
    permissions = property(_get_permissions)

    def _get_groups(self):
        '''Get set of group names of this identity.'''
        try:
            return self._groups
        except AttributeError:
            # Groups haven't been computed yet
            pass
        if not self.user:
            self._groups = frozenset()
        else:
            ### TG: Difference.  Our model has a many::many for people:groups
            # And an association proxy that links them together
            self._groups = frozenset([g.name for g in self.user.approved_memberships])
        return self._groups
    groups = property(_get_groups)

    def _get_group_ids(self):
        '''Get set of group IDs of this identity.'''
        try:
            return self._group_ids
        except AttributeError:
            # Groups haven't been computed yet
            pass
        if not self.user:
            self._group_ids = frozenset()
        else:
            ### TG: Difference.  Our model has a many::many for people:groups
            # And an association proxy that links them together
            self._group_ids = frozenset([g.id for g in self.user.approved_memberships])
        return self._group_ids
    group_ids = property(_get_group_ids)

    ### TG: Same as TG-1.0.8
    def _get_visit_link(self):
        '''Get the visit link to this identity.'''
        if self._visit_link:
            return self._visit_link
        if self.visit_key is None:
            self._visit_link = None
        else:
            self._visit_link =  visit_class.query.filter_by(visit_key=self.visit_key).first()
        return self._visit_link
    visit_link = property(_get_visit_link)

    ### TG: Same as TG-1.0.8
    def _get_login_url(self):
        '''Get the URL for the login page.'''
        return identity.get_failure_url()
    login_url = property(_get_login_url)

    ### TG: Same as TG-1.0.8
    def login(self, using_ssl=False):
        '''Set the link between this identity and the visit.'''
        visit = self.visit_link
        if visit:
            visit.user_id = self._user.id
            visit.ssl = using_ssl
        else:
            visit = visit_class()
            visit.visit_key = self.visit_key
            visit.user_id = self._user.id
            visit.ssl = using_ssl
        session.flush()

    ### TG: Same as TG-1.0.8
    def logout(self):
        '''Remove the link between this identity and the visit.'''
        visit = self.visit_link
        if visit:
            session.delete(visit)
            session.flush()
        # Clear the current identity
        identity.set_current_identity(SaFasIdentity())

class SaFasIdentityProvider(object):
    '''
    IdentityProvider that authenticates users against the fedora account system
    '''
    def __init__(self):
        super(SaFasIdentityProvider, self).__init__()

        global user_class
        global visit_class

        user_class_path = config.get("identity.saprovider.model.user", None)
        user_class = load_class(user_class_path)
        visit_class_path = config.get("identity.saprovider.model.visit", None)
        log.info(_("Loading: %(visitmod)s") % \
                {'visitmod': visit_class_path})
        visit_class = load_class(visit_class_path)

    def create_provider_model(self):
        '''
        Create the database tables if they don't already exist.
        '''
        class_mapper(user_class).local_table.create(checkfirst=True)
        class_mapper(visit_class).local_table.create(checkfirst=True)

    def validate_identity(self, user_name, password, visit_key, otp=None):
        '''
        Look up the identity represented by user_name and determine whether the
        password is correct.

        Must return either None if the credentials weren't valid or an object
        with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs

        Side Effects:
        :cherrypy.request.fas_provided_username: set to user_name
        :cherrypy.request.fas_identity_failure_reason: if we fail to validate
            the user, set to the reason validation failed.  Values can be:
            :no_user: The username was not present in the db.
            :status_inactive: User is disabled but can reset their password
                to restore service.
            :status_expired: User is expired, account is no more.
            :status_admin_disabled: User is disabled and has to talk to an
                admin before they are re-enabled.
            :bad_password: The username and password do not match.

        Arguments:
        :arg user_name: user_name we're authenticating.  If None, we'll try
            to lookup a username from SSL variables
        :arg password: password to authenticate user_name with
        :arg visit_key: visit_key from the user's session
        :arg otp: One Time Password key to authenticate within the password
        '''
        # Save the user provided username so we can do other checks on it in
        # outside of this method.
        cherrypy.request.fas_provided_username = user_name
        cherrypy.request.fas_identity_failure_reason = None
        using_ssl = False

        if not user_name:
            if cherrypy.request.headers['X-Client-Verify'] == 'SUCCESS':
                user_name = cherrypy.request.headers['X-Client-CN']
                cherrypy.request.fas_provided_username = user_name
                using_ssl = True

        email_domain = '@' + config.get('email_host', '')
        if email_domain != '@' and user_name.endswith(email_domain):
            user_name = user_name[:-len(email_domain)]

        if '@' in user_name:
            user = user_class.query.filter_by(email=user_name).first()
        else:
            user = user_class.query.filter_by(username=user_name).first()

        if not user:
            log.warning("No such user: %s", user_name)
            cherrypy.request.fas_identity_failure_reason = 'no_user'
            return None

        if user.status in ('inactive', 'expired', 'admin_disabled'):
            log.warning("User %(username)s has status %(status)s" %
                {'username': user_name, 'status': user.status})
            cherrypy.request.fas_identity_failure_reason = 'status_%s'% user.status
            return None

        if not using_ssl:
            if 'otp' in cherrypy.request.params:
                otp = cherrypy.request.params.pop('otp')

            if not self.validate_password(user, user_name, password, otp):
                log.info("Passwords don't match for user: %s", user_name)
                cherrypy.request.fas_identity_failure_reason = 'bad_password'
                return None
            # user + password is sufficient to prove the user is in
            # control
            cherrypy.request.params['_csrf_token'] = hash_constructor(
                    visit_key).hexdigest()

        log.info("Associating user (%s) with visit (%s)",
            user_name, visit_key)
        user.last_seen = datetime.now(pytz.utc)
        return SaFasIdentity(visit_key, user, using_ssl)

    def validate_password(self, user, user_name, password, otp=None):
        '''
        Check the supplied user_name and password against existing credentials.
        Note: user_name is not used here, but is required by external
        password validation schemes that might override this method.
        If you use SaFasIdentityProvider, but want to check the passwords
        against an external source (i.e. PAM, LDAP, Windows domain, etc),
        subclass SaFasIdentityProvider, and override this method.

        :user: User information.  Not used.
        :user_name: Given username.
        :password: Given plaintext password.
        :otp: Given OTP (one time password)
        :returns: True if the password matches the username.  Otherwise False.
            Can return False for problems within the Account System as well.
        '''
        # crypt.crypt(stuff, '') == ''
        # Just kill any possibility of blanks.
        if not user.password:
            return False
        if not password:
            return False

        user.password == crypt.crypt(password.encode('utf-8'), user.password)

        # Check if combo login (password+otp) has been requested.
        if otp:
            if otp_check(otp):
                if otp_validate(user_name, otp) and user.password:
                    return True
                else:
                    log.debug('Invalid OTP or password!')

        # TG identity providers take user_name in case an external provider
        # needs it so we can't get rid of it. (W0613)
        # pylint: disable-msg=W0613
        return user.password

    def load_identity(self, visit_key):
        '''Lookup the principal represented by visit_key.

        :arg visit_key: The session key for whom we're looking up an identity.
        :return: an object with the following properties:
            :user_name: original user name
            :user: a provider dependant object (TG_User or similar)
            :groups: a set of group IDs
            :permissions: a set of permission IDs
        '''
        ident = SaFasIdentity(visit_key)
        if 'csrf_login' in cherrypy.request.params:
            cherrypy.request.params.pop('csrf_login')
            set_login_attempted(True)
        return ident

    def anonymous_identity(self):
        '''Returns an anonymous user object

        :return: an object with the following properties:
            :user_name: original user name
            :user: a provider dependant object (TG_User or similar)
            :groups: a set of group IDs
            :permissions: a set of permission IDs
        '''
        return SaFasIdentity(None)

    def authenticated_identity(self, user):
        '''
        Constructs Identity object for user that has no associated visit_key.

        :arg user: The user structure the identity is constructed from
        :return: an object with the following properties:
            :user_name: original user name
            :user: a provider dependant object (TG_User or similar)
            :groups: a set of group IDs
            :permissions: a set of permission IDs
        '''
        return SaFasIdentity(None, user)
