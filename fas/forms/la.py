# -*- coding: utf-8 -*-

from wtforms import (
    Form,
    StringField,
    TextAreaField,
    validators
    )

from fas.utils import _
from fas.models import provider as provider

class EditLicenseForm(Form):
    """ Form to  add, edit and validate license agreement infos."""
    name = StringField(_(u'Name'), [validators.Required()])
    content = TextAreaField(_(u'Text'), [validators.Required()])
    comment = StringField(_(u'Comments'), [validators.Optional()])
