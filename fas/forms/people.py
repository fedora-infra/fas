# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Xavier Lamien.
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
__author__ = ['Xavier Lamien <laxathom@fedoraproject.org>',
              'Pierre-Yves Chibon <pingou@fedoraproject.org>']

from fas.util import _, Config
from fas.models import AccountStatus
from fas.models import provider

from wtforms import (
    Form,
    HiddenField,
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    IntegerField,
    DecimalField,
    PasswordField,
    validators,
    ValidationError
    )

from pytz import common_timezones

import calendar


# Yes we do nothing with the form argument but it's required...
# pylint: disable=W0613
def is_number(form, field):
    ''' Check if the data in the field is a number and raise an exception
    if it is not.
    '''
    if not field.data:
        return
    try:
        float(field.data)
    except ValueError:
        raise ValidationError(_(u'Field must contain a number'))


def check_availibility(key):
    """ Check field availibility from registered list.

    Requires: field username in your class definition.
    """
    __data__ = getattr(provider, 'get_people_%s' % key)

    def __validate__(form, field):
        """ Validata that field value is not stored already. """
        avail_data = [value[0] for value in __data__(form.username.data)]

        if field.data in avail_data:
            raise ValidationError(_(u'%s exists already!' % field.data))

    return __validate__


def check_blacklist():
    """ Check username against policy."""
    def __validate__(form, field):
        """ Validate username field"""
        if field.data in Config.get('blacklist.username').split(','):
            raise ValidationError(
                _(u'%s is not allowed!' % field.data))

    return __validate__


class UpdateStatusForm(Form):
    """ Form to update people\'s status"""
    status = SelectField(
        _(u'Status'),
        [validators.Required()],
        coerce=int,
        choices=[(e.value, e.name.lower()) for e in AccountStatus])


class PeopleForm(Form):
    """ Simple form to select registered people. """
    people = SelectField(
        _(u'Select a user'),
        [validators.Required()],
        coerce=int
    )

    def __init__(self, *args, **kwargs):
        super(PeopleForm, self).__init__(*args, **kwargs)
        # Initialize choices here so we load this every time instead of
        # upon startup
        self.people.choices = [
            (u.id, u.username + ' (' + u.fullname + ')')
            for u in provider.get_people()
        ]


class UsernameForm(Form):
    """ Simple form to request the user's username. """
    username = StringField(_(u'Username'),
        [validators.Required(),
            check_availibility(key='username'),
            check_blacklist()])


class EmailForm(Form):
    """ Form to validate email. """
    email = StringField(
        _(u'Email'),
        [validators.Required(),
            validators.Email(),
            check_availibility(key='email')])


class ContactInfosForm(EmailForm):
    """ Form to edit contact infos. """
    username = HiddenField()
    fullname = StringField(_(u'Full name'), [validators.Required()])
    facsimile = StringField(_(u'Facsimile'))
    telephone = StringField(_(u'Telephone number'))
    postal_address = StringField(_(u'Postal address'), [validators.Optional()])
    affiliation = StringField(_(u'Affiliation'), [validators.Optional()])
    country_code = SelectField(
        _(u'Country code'),
        [validators.Required()],
        coerce=str,
        choices=[(-1, _(u'-- None --'))])


class ResetPasswordPeopleForm(Form):
    """ Form to used to reset one's password. """
    new_password = PasswordField(
        _(u'New Password'),
        [validators.Required(), validators.EqualTo(
            'password', message='Your passwords must match')])
    password = PasswordField(
        _(u'Confirm new Password'), [validators.Required()])


class UpdatePasswordForm(ResetPasswordPeopleForm):
    """ Form to update people password."""
    old_password = PasswordField(
        _(u'Old Password'),
        [validators.Required()])


class EditPeopleForm(UpdateStatusForm, UsernameForm, ContactInfosForm):
    """ Form to edit user's information. """
    introduction = StringField(_(u'Introduction'), [validators.Optional()])
    ircnick = StringField(_(u'IRC nick'), [check_availibility('ircnick')])
    avatar = StringField(_(u'Avatar'))
    birthday = IntegerField(
        _(u'Birthday'), [validators.Optional()], default=-1)
    birthday_month = SelectField(
        _(u'Month'),
        [validators.Optional()],
        choices=[(m, m) for m in calendar.month_name if m is not None])
    bio = TextAreaField(_(u'Introduction'), [validators.Optional()])
    # FIXME: actually retrieve the list of locales available
    locale = SelectField(
        _(u'Locale'),
        [validators.Required()],
        coerce=str,
        choices=[(-1, _(u'-- None --'))])
    timezone = SelectField(
        _(u'Timezone'),
        [validators.Required()],
        choices=[(tzone, tzone) for tzone in common_timezones])
    gpg_fingerprint = StringField(_(u'GPG Fingerprint'))
    ssh_key = StringField(_(u'Public SSH Key'))
    bugzilla_email = StringField(_(u'Bugzilla email'),
        [validators.Optional(),
            validators.Email(),
            check_availibility(key='bugzilla_email')])
    privacy = BooleanField(_(u'Privacy'))
    blog_rss = StringField(_(u'Blog RSS'), [validators.Optional()])
    latitude = DecimalField(_(u'Latitude'), [validators.Optional()])
    longitude = DecimalField(_(u'Longitude'), [validators.Optional()])


class NewPeopleForm(UsernameForm, EmailForm):
    """ Form to create an user's account. """
    fullname = StringField(_(u'Full name'), [validators.Required()])
    password = PasswordField(
        _(u'Password'),
        [validators.Required(), validators.EqualTo(
            'password_confirm', message='Your new passwords must match')])
    password_confirm = PasswordField(
        _(u'Confirm new Password'), [validators.Required()])


class UpdateAvatarForm(Form):
    """ Form to update people\'s avatar"""
    avatar_id = StringField(_(u'Avatar ID'), [validators.Required()])


class UpdateSshKeyForm(Form):
    """ Form to update ssh key"""
    ssh_key = TextAreaField(_(u'ssh key'), [validators.Optional()])


class UpdateGpgFingerPrint(Form):
    """ Form to edit GPG Fingerprint. """
    gpg_fingerprint = StringField(
        _(u'GPG Fingerprint'), [validators.Optional()])
