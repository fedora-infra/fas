# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
#
# Copyright © 2014 Xavier Lamien.
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
    TextAreaField,
    IntegerField,
    BooleanField,
    SelectField,
    validators
    )

from fas.util import _


class EditLicenseForm(Form):
    """ Form to  add, edit and validate license agreement infos."""
    name = StringField(_(u'Name'), [validators.Required()])
    content = TextAreaField(_(u'Text'), [validators.Required()])
    comment = StringField(_(u'Comments'), [validators.Optional()])
    enabled_at_signup = BooleanField(
        _(u'Required at sign-up'), [validators.Optional()])


class SignLicenseForm(Form):
    """ Form to validate signed license agreement from registered people."""
    license = IntegerField(_(u'License Agreement'), [validators.Optional()])
    people = IntegerField(_(u'People Id'), [validators.Optional()])
    signed = BooleanField(_(u'I agree to the terms of the license'),
        [validators.Required()])


class LicenseListForm(Form):
    """ Form to select valid license agreement name. """
    id = SelectField(
        _(u'Select a license'),
        [validators.Required()],
        coerce=int,
        choices=[(-1, _(u'-- None --'))])
