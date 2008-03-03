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
This plugin provides authentication of passwords against the Fedora Account
System.
'''



from sqlalchemy.orm import class_mapper
from turbogears import config, identity
from turbogears.identity.saprovider import SqlAlchemyIdentity, \
        SqlAlchemyIdentityProvider
from turbogears.database import session
from turbogears.util import load_class

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

# Global class references --
# these will be set when the provider is initialised.
user_class = None
visit_identity_class = None

class SaFasIdentity(SqlAlchemyIdentity):
    def __init__(self, visit_key, user=None):
        super(SaFasIdentity, self).__init__(visit_key, user)

    def _get_user(self):
        try:
            return self._user
        except AttributeError:
            # User hasn't already been set
            pass
        # Attempt to load the user. After this code executes, there *WILL* be
        # a _user attribute, even if the value is None.
        ### TG: Difference: Can't use the inherited method b/c of global var
        visit = visit_identity_class.query.filter_by(visit_key = self.visit_key).first()
        if not visit:
            self._user = None
            return None
        self._user = user_class.query.get(visit.user_id)
        return self._user
    user = property(_get_user)

    def _get_user_name(self):
        if not self.user:
            return None
        ### TG: Difference: Different name for the field
        return self.user.username
    user_name = property(_get_user_name)

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

    def logout(self):
        '''
        Remove the link between this identity and the visit.
        '''
        if not self.visit_key:
            return
        try:
            ### TG: Difference: Can't inherit b/c this uses a global var
            visit = visit_identity_class.query.filter_by(visit_key=self.visit_key).first()
            session.delete(visit)
            # Clear the current identity
            anon = SqlAlchemyIdentity(None,None)
            identity.set_current_identity(anon)
        except:
            pass
        else:
            session.flush()

class SaFasIdentityProvider(SqlAlchemyIdentityProvider):
    '''
    IdentityProvider that authenticates users against the fedora account system
    '''
    def __init__(self):
        global visit_identity_class
        global user_class

        user_class_path = config.get("identity.saprovider.model.user", None)
        user_class = load_class(user_class_path)
        visit_identity_class_path = config.get("identity.saprovider.model.visit", None)
        log.info(_("Loading: %(visitmod)s") % \
                {'visitmod': visit_identity_class_path})
        visit_identity_class = load_class(visit_identity_class_path)

    def create_provider_model(self):
        '''
        Create the database tables if they don't already exist.
        '''
        class_mapper(user_class).local_table.create(checkfirst=True)
        class_mapper(visit_identity_class).local_table.create(checkfirst=True)

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
        user = user_class.query.filter_by(username=user_name).first()
        if not user:
            log.warning("No such user: %s", user_name)
            return None
        if not self.validate_password(user, user_name, password):
            log.info("Passwords don't match for user: %s", user_name)
            return None

        log.info("associating user (%s) with visit (%s)", user.username,
                  visit_key)
        # Link the user to the visit
        link = visit_identity_class.query.filter_by(visit_key=visit_key).first()
        if not link:
            link = visit_identity_class()
            link.visit_key = visit_key
            link.user_id = user.id
        else:
            link.user_id = user.id
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
