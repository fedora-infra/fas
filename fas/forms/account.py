# -*- coding: utf-8 -*-
#
# Copyright © 2015 Xavier Lamien.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from wtforms import (
    Form,
    StringField,
    RadioField,
    validators,
    SelectField)

from fas.models import AccountPermissionType

from fas.util import _


class AccountPermissionForm(Form):
    """ Form to select valid account's permissions. """
    desc = StringField(_(u'Description'), [validators.Required()])
    perm = RadioField(
        _('Accounts permissions'),
        [validators.Required()],
        coerce=int,
        choices=[(perm.value, perm.name) for perm in AccountPermissionType]
        )


class TrustedPermissionForm(Form):
    """Form to select valid trusted permissions ."""
    id = SelectField(
        _(u'Select a trusted permissions app'),
        [validators.Required()],
        coerce=int,
        choices=[(-1, _(u'-- None --'))])