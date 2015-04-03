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

