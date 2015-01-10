# -*- coding: utf-8 -*-

from wtforms import (
    Form,
    StringField,
    TextAreaField,
    BooleanField,
    IntegerField,
    SelectField,
    validators
    )

from fas.utils import _


class EditCertificateForm(Form):
    """ Form to edit certificates. """
    name = StringField(_(u'Certificate Name'), [validators.Required()])
    description = StringField(_(u'Description'), [validators.Optional()])
    country = StringField(_(u'Country Name (C)'), [validators.Optional()])
    state = StringField(_(u'State Name (ST)'), [validators.Optional()])
    locality = StringField(_(u'Locality Name (L)'), [validators.Optional()])
    common_name = StringField(_(u'Common Name (CN)'), [validators.Optional()])
    cert = TextAreaField(_(u'Certficate pubkey'), [validators.Required()])
    cert_key = TextAreaField(_(u'Certificate privkey'), [validators.Required()])
    client_cert_desc = StringField(
        _(u'Certificate Client Description'),
        [validators.Optional()])
    enabled = BooleanField(
        _(u'Enable certificate'),
        [validators.Optional()])
    organization = StringField(
        _(u'Organization Name (O)'),
        [validators.Optional()])
    organizational_unit = StringField(
        _(u'Organizational Unit (OU)'),
        [validators.Optional()])


class CreateClientCertificateForm(Form):
    """ Form to deal with clients certificates. """
    cacert = IntegerField(
        _(u'Certificate Authority/Server'),
        [validators.Required()])
    client_cert_desc = StringField(
        _(u'Client certifiate description'),
        [validators.Optional()])
    group_id = IntegerField(
        _(u'Group ID'),
        [validators.Required()])
    group_name = StringField(_(u'Group name'), [validators.Optional()])

