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
# Author(s): Toshio Kuratomi <tkuratom@redhat.com>
#            Ricky Zhou <ricky@fedoraproject.org>
#

'''
This plugin provides authentication of passwords against the Fedora Account
System.
'''

from sqlalchemy.orm import class_mapper
from turbogears import config, identity
from turbogears.database import session
from turbogears.util import load_class

import cherrypy

import gettext
t = gettext.translation('fas', '/usr/share/locale', fallback=True)
_ = t.ugettext

import crypt

import logging
log = logging.getLogger('turbogears.identity.safasprovider')

try:
    set, frozenset
except NameError:
    # We need a set type on earlier pythons. (W0622)
    from sets import Set as set # pylint: disable-msg=W0622
    from sets import ImmutableSet as frozenset # pylint: disable-msg=W0622

# Global class references --
# these will be set when the provider is initialised.
user_class = None
visit_class = None

class SaFasIdentity(object):
    def __init__(self, visit_key, user=None):
        if user:
            self._user = user
        self.visit_key = visit_key

    def _get_user(self):
        try:
            return self._user
        except AttributeError:
            # User hasn't already been set
            pass
        # Attempt to load the user. After this code executes, there *WILL* be
        # a _user attribute, even if the value is None.
        visit = visit_class.query.filter_by(visit_key=self.visit_key).first()
        if not visit:
            self._user = None
            return None
        # I hope this is a safe place to double-check the SSL variables.
        # TODO: Double check my logic with this - is it unnecessary to
        # check that the username matches up?
        if visit.ssl:
            if cherrypy.request.headers['X-Client-Verify'] != 'SUCCESS':
                self.logout()
                return None
        self._user = user_class.query.get(visit.user_id)
        visit = visit_class.query.filter_by(visit_key=self.visit_key).first()
        if self._user.status in ('inactive', 'admin_disabled'):
            log.warning("User %(username)s has status %(status)s, logging them out." % \
                { 'username': self._user.username, 'status': self._user.status })
            self.logout()
            None

        return self._user
    user = property(_get_user)

    def _get_user_name(self):
        if not self.user:
            return None
        ### TG: Difference: Different name for the field
        return self.user.username
    user_name = property(_get_user_name)

    ### TG: Same as TG-1.0.4.3
    def _get_anonymous(self):
        return not self.user
    anonymous = property(_get_anonymous)

    ### TG: Same as TG-1.0.4.3
    def _get_permissions(self):
        try:
            return self._permissions
        except AttributeError:
            # Permissions haven't been computed yet
            pass
        if not self.user:
            self._permissions = frozenset()
        else:
            self._permissions = frozenset([
                p.permission_name for p in self.user.permissions])
        return self._permissions
    permissions = property(_get_permissions)

    def _get_groups(self):
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

    ### TG: same as TG-1.0.4.3
    def logout(self):
        '''
        Remove the link between this identity and the visit.
        '''
        if not self.visit_key:
            return
        try:
            visit = visit_class.query.filter_by(visit_key=self.visit_key).first()
            session.delete(visit)
            # Clear the current identity
            anon = SaFasIdentity(None,None)
            identity.set_current_identity(anon)
        except:
            pass
        else:
            session.flush()

class SaFasIdentityProvider(object):
    '''
    IdentityProvider that authenticates users against the fedora account system
    '''
    def __init__(self):
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

        Side Effects:
        :cherrypy.request.fas_provided_username: set to user_name
        :cherrypy.request.fas_identity_failure_reason: if we fail to validate
            the user, set to the reason validation failed.  Values can be:
            :no_user: The username was not present in the db.
            :status_inactive: User is disabled but can reset their password
                to restore service.
            :status_admin_disabled: User is disabled and has to talk to an
                admin before they are re-enabled.
            :bad_password: The username and password do not match.
        '''
        # Save the user provided username so we can do other checks on it in
        # outside of this method.
        cherrypy.request.fas_provided_username = user_name
        cherrypy.request.fas_identity_failure_reason = None
        using_ssl = False
        if not user_name:
            if cherrypy.request.headers['X-Client-Verify'] == 'SUCCESS':
                user_name = cherrypy.request.headers['X-Client-CN']
                using_ssl = True
        user = user_class.query.filter_by(username=user_name).first()
        if not user:
            log.warning("No such user: %s", user_name)
            cherrypy.request.fas_identity_failure_reason = 'no_user'
            return None

        if user.status in ('inactive', 'admin_disabled'):
            log.warning("User %(username)s has status %(status)s" % \
                { 'username': user_name, 'status': user.status })
            cherrypy.request.fas_identity_failure_reason = 'status_%s' \
                    % user.status
            return None

        if not using_ssl:
            if not self.validate_password(user, user_name, password):
                log.info("Passwords don't match for user: %s", user_name)
                cherrypy.request.fas_identity_failure_reason = 'bad_password'
                return None

        log.info("associating user (%s) with visit (%s)", user.username,
                  visit_key)
        # Link the user to the visit
        link = visit_class.query.filter_by(visit_key=visit_key).first()
        if not link:
            link = visit_class()
            link.visit_key = visit_key
            link.user_id = user.id
            link.ssl = using_ssl
        else:
            link.user_id = user.id
            link.ssl = using_ssl
        session.flush()
        return SaFasIdentity(visit_key, user)

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
        # TG identity providers take user_name in case an external provider
        # needs it so we can't get rid of it. (W0613)
        # pylint: disable-msg=W0613
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
        return SaFasIdentity(visit_key)

    def anonymous_identity(self):
        '''
        Must return an object with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''

        return SaFasIdentity(None)

    def authenticated_identity(self, user):
        '''
        Constructs Identity object for user that has no associated visit_key.
        '''
        return SaFasIdentity(None, user)
