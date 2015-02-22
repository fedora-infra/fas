# -*- coding: utf-8 -*-

from wtforms import (
    Form,
    StringField,
    RadioField,
    validators,
    SelectField)

from fas.models import AccountPermissionType

from fas.utils import _


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