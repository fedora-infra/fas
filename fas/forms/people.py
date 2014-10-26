# -*- coding: utf-8 -*-

from fas.utils import _
from fas.models import AccountStatus

from wtforms import (
    Form,
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
        raise ValidationError(
            'Field must contain a number')


class UpdateStatusForm(Form):
    """ Form to update people\'s status"""
    # TODO: filter out status user are not allowed to select.
    status = SelectField(
        _(u'Status'),
        [validators.Required()],
        choices=[(e.value, e.name.lower()) for e in AccountStatus])


class UsernameForm(Form):
    """ Simple form to request the user's username. """
    username = StringField(_(u'Username'), [validators.Required()])


class ContactInfosForm(Form):
    """ Form to edit contact infos. """
    fullname = StringField(_(u'Full name'), [validators.Required()])
    email = StringField(
        _(u'Email'), [validators.Required(), validators.Email()])
    facsimile = StringField(_(u'Facsimile'))
    telephone = StringField(_(u'Telephone number'))
    postal_address = StringField(_(u'Postal address'), [validators.Optional()])
    affiliation = StringField(_(u'Affiliation'), [validators.Optional()])
    country_code = SelectField(
        _(u'Country code'),
        [validators.Required()],
        coerce=str,
        choices=[('FR', 'France (FR)'), ('JP', 'Japan (JP)')])


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
    ircnick = StringField(_(u'IRC nick'))
    avatar = StringField(_(u'Avatar'))
    birthday = IntegerField(
        _(u'Birthday'), [validators.Optional()], default=-1)
    birthday_month = SelectField(
        _(u'Month'),
        choices=[(m, m) for m in calendar.month_name if m is not None])
    bio = TextAreaField(_(u'Introduction'))
    # FIXME: actually retrieve the list of locales available
    locale = SelectField(
        _(u'Locale'),
        [validators.Required()],
        choices=[('en', 'en'), ('fr', 'fr')], coerce=str)
    timezone = SelectField(
        _(u'Timezone'),
        [validators.Required()],
        choices=[(tzone, tzone) for tzone in common_timezones])
    gpg_id = StringField(_(u'GPG Key'))
    gpg_fingerprint = StringField(_(u'GPG Fingerprint'))
    ssh_key = StringField(_(u'Public SSH Key'))
    bugzilla_email = StringField(_(u'Bugzilla email'))
    privacy = BooleanField(_(u'Privacy'))
    blog_rss = StringField(_(u'Blog RSS'))
    latitude = DecimalField(_(u'Latitude'), [validators.Optional()])
    longitude = DecimalField(_(u'Longitude'), [validators.Optional()])


class NewPeopleForm(UsernameForm):
    """ Form to create an user's account. """
    fullname = StringField(_(u'Full name'), [validators.Required()])
    email = StringField(
        _(u'Email'), [validators.Required(), validators.Email()])
    password = PasswordField(
        _(u'Password'),
        [validators.Required(), validators.EqualTo(
            'password_confirm', message='Your new passwords must match')])
    password_confirm = PasswordField(
        _(u'Confirm new Password'), [validators.Required()])
