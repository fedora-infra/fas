# -*- coding: utf-8 -*-
#
# Copyright © 2011 Red Hat, Inc.
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
#
'''Controller for dealing with configs stored in the database for other apps.

Some services in Fedora do not have their own database to store information
about themselves.  When these apps need to store per user data we save the
information in the FAS2 configs table.  The methods defined here are for
generic access to that information.  Most apps would want to provide a FAS
plugin that allows easier access to the configs via a specificly written
template instead of using the generic interface.
'''

from sqlalchemy.sql import and_
from sqlalchemy.exc import InvalidRequestError, DBAPIError

from turbogears import validate, validators, controllers, expose, flash, \
        error_handler, identity, redirect
from turbogears.database import session

from fedora.tg.utils import request_format

from fas.model import Configs, People
from fas.validators import KnownUser
from fas.auth import can_edit_user

from fas import _

class ConfigList(validators.Schema):
    '''Set of validators for the list method of Configs'''
    # pylint: disable-msg=W0232,R0903
    def __init__(self):
        self.username = KnownUser

    application = validators.All(validators.UnicodeString,
            validators.Regex(regex='^[a-z0-9-_]+$'),
            # This could also match the db precisely.  But then we'd have to
            # keep them synced:
            #validators.OneOf(('asterisk', 'moin', 'myfedora', 'openid',
            #        'bugzilla'))
            )
    pattern = validators.UnicodeString

class ConfigSet(validators.Schema):
    '''Set of validators for the set method of Configs'''
    # pylint: disable-msg=W0232,R0903
    username = KnownUser
    application = validators.All(validators.UnicodeString,
            validators.Regex(regex='^[a-z0-9-_]+$'),
            # This could also match the db precisely.  But then we'd have to
            # keep them synced:
            #validators.OneOf(('asterisk', 'moin', 'myfedora', 'openid',
            #        'bugzilla'))
            )
    attribute = validators.UnicodeString
    value = validators.UnicodeString

class Config(controllers.Controller):
    '''Controller that serves generic third party app configs.
    '''

    def __init__(self):
        pass

    @expose(template="fas.templates.error", allow_json=True)
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        # Only tg controller methods are served via the web so we have to have
        # methods even if they could be functions. (R0201)
        # pylint: disable-msg=R0201

        ### FIXME: This can be made simpler once we have a new python-fedora
        # with jsonify_validation_errors()
        if tg_errors:
            if request_format() == 'json':
                message = '\n'.join([u'%s: %s' % (param, msg) for param, msg in
                    tg_errors.items()])
                return dict(exc='Invalid', tg_flash=message, tg_template='json')
        if not tg_errors:
            # We should only reach this if the user hit the url manually.
            if request_format() == 'json':
                return dict()
            else:
                redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(identity.not_anonymous())
    @validate(validators=ConfigList())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(allow_json=True)
    def list(self, username, application, pattern=u'*'):
        '''Retrieve configs for a user and application.

        Arguments:
        :username: owner of the configs we're searching for
        :application: program that the configs are for
        :pattern: Limit the configs to ones which match this pattern. '*' is a
            wildcard character

        Returns: dict that maps the name of the config attribute to the config
            value.
        '''
        # Only tg controller methods are served via the web so we have to have
        # methods even if they could be functions. (R0201)
        # pylint: disable-msg=R0201

        # Verify user is allowed to view this config
        target = People.by_username(username)
        if not can_edit_user(identity.current.user, target):
            flash(_('You cannot look at configs for %s') % username)
            if request_format() == 'json':
                return dict(exc='AuthorizationError')
            else:
                redirect('/')

        # This only works if pattern is unicode.  But it should be unicode
        # because of the validator.
        pattern = pattern.translate({ord(u'*'): ur'%'}).lower()

        # Retrieve the data and reformat it as a dict keyed on attribute
        # pylint: disable-msg=E1101
        cfgs = Configs.query.filter_by(application=application).filter(
                and_(Configs.attribute.like(pattern),
                    People.username==username))
        # pylint: enable-msg=E1101
        results = dict((cfg.attribute, cfg.value) for cfg in cfgs.all())

        return dict(username=username, application=application,
                pattern=pattern, configs=results)

    @identity.require(identity.not_anonymous())
    @validate(validators=ConfigSet())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(allow_json=True)
    def set(self, username, application, attribute, value=None):
        '''Retrieve configs for a user and application.

        Arguments:
        :username: owner of the configs we're searching for
        :application: program that the configs are for
        :attribute: name of the option we're setting
        :value: value to set in the db.  If ths is None, we won't set anything
        '''
        # Only tg controller methods are served via the web so we have to have
        # methods even if they could be functions. (R0201)
        # pylint: disable-msg=R0201

        # Verify user is allowed to set this config
        target = People.by_username(username)
        if not can_edit_user(identity.current.user, target):
            flash(_('You cannot edit configs for %s') % username)
            if request_format() == 'json':
                return dict(exc='AuthorizationError')
            else:
                redirect('/')

        # Retrieve the data and reformat it as a dict keyed on attribute
        try:
            # pylint: disable-msg=E1101
            config = Configs.query.filter_by(application=application,
                    attribute=attribute).filter(People.username==username).one()
            config.value = value
        except InvalidRequestError:
            # There was no Config, create a new one
            config = Configs(application=application, attribute=attribute,
                    value=value)
            # pylint: disable-msg=E1101
            config.person = People.query.filter_by(username=username).one()

        try:
            # ScopedSession really does have a flush() method
            # pylint: disable-msg=E1101
            session.flush()
        except DBAPIError, error:
            flash(_('Error saving the config to the database: %s' % (error)))
            return dict(exc='DBAPIError')

        # On success return an empty dict
        flash(_('Config value successfully updated'))
        return {}
