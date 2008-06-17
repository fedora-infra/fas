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
#            Toshio Kuratomi <tkuratom@redhat.com>
#
'''Collection of validators for parameters coming to FAS URLs.'''

# Validators don't need an __init__ method (W0232)
# Validators are following an API specification so need methods that otherwise
#   would be functions (R0201)
# Validators will usu. only have two methods (R0903)
# pylint: disable-msg=W0232,R0201,R0903

# Disabled inline for specific cases:
# Validators will have a variable "state" that is very seldom used (W0163)
# Validator methods don't really need docstrings since the validator docstring
#   pretty much covers it (C0111)

import re
# This assigns a value to "_"
# pylint: disable-msg=W0611
import turbogears
# pylint: enable-msg=W0611
from turbogears import validators, config
from sqlalchemy.exceptions import InvalidRequestError
from fas.util import available_languages

from fas.model import People, Groups

class KnownGroup(validators.FancyValidator):
    '''Make sure that a group already exists'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        try:
            # Just make sure the group already exists
            # pylint: disable-msg=W0612
            group = Groups.by_name(value)
        except InvalidRequestError:
            raise validators.Invalid(_("The group '%s' does not exist.")
                    % value, value, state)

class UnknownGroup(validators.FancyValidator):
    '''Make sure that a group doesn't already exist'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        try:
            # Just make sure the group doesn't already exist
            # pylint: disable-msg=W0612
            group = Groups.by_name(value)
        except InvalidRequestError:
            pass
        else:
            raise validators.Invalid(_("The group '%s' already exists.")
                    % value, value, state)

class ValidGroupType(validators.FancyValidator):
    '''Make sure that a group type is valid'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if value not in ('system', 'bugzilla', 'cvs', 'bzr', 'git', \
            'hg', 'mtn', 'svn', 'shell', 'torrent', 'tracker', \
            'tracking', 'user'):
            raise validators.Invalid(_("Invalid group type.") % value,
                    value, state)

class KnownUser(validators.FancyValidator):
    '''Make sure that a user already exists'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        try:
            # just prove that we can retrieve a person for the username
            # pylint: disable-msg=W0612
            people = People.by_username(value)
        except InvalidRequestError:
            # pylint: disable-msg=E0602
            raise validators.Invalid(_("'%s' does not exist.") % value,
                    value, state)

class UnknownUser(validators.FancyValidator):
    '''Make sure that a user doesn't already exist'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        try:
            # just prove that we *cannot* retrieve a person for the username
            # pylint: disable-msg=W0612
            people = People.by_username(value)
        except InvalidRequestError:
            return
        except:
            # pylint: disable-msg=E0602
            raise validators.Invalid(_("Error: Could not create - '%s'") %
                    value, value, state)

        raise validators.Invalid(_("'%s' already exists.") % value,
                value, state)

class NonFedoraEmail(validators.FancyValidator):
    '''Make sure that an email address is not @fedoraproject.org'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if value.endswith('@fedoraproject.org'):
            raise validators.Invalid(_("To prevent email loops, your email"
                    " address cannot be @fedoraproject.org."), value, state)

class ValidSSHKey(validators.FancyValidator):
    ''' Make sure the ssh key uploaded is valid '''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.file.read()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
#        value = value.file.read()
        keylines = value.split('\n')
        for keyline in keylines:
            if not keyline:
                continue
            keyline = keyline.strip()
            validline = re.match('^(rsa|ssh-rsa) [ \t]*[^ \t]+.*$', keyline)
            if not validline:
                raise validators.Invalid(_('Error - Not a valid RSA SSH key:'
                        ' %s') % keyline, value, state)

class ValidUsername(validators.FancyValidator):
    '''Make sure that a username isn't blacklisted'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        username_blacklist = config.get('username_blacklist')
        if re.compile(username_blacklist).match(value):
            raise validators.Invalid(_("'%s' is an illegal username.  A valid"
                " username must only contain lowercase alphanumeric"
                " characters, and must start with a letter.") % value,
                value, state)

class ValidLanguage(validators.FancyValidator):
    '''Make sure that a username isn't blacklisted'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if value not in available_languages():
            raise validators.Invalid(_('The language \'%s\' is not available.')
                  % value, value, state)
