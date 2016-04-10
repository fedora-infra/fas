# -*- coding: utf-8 -*-
#
# Copyright © 2014-2016 Xavier Lamien.
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
# __author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from wtforms import (
    Form,
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    validators
    )

# from wtforms.ext.sqlalchemy.fields import QuerySelectField

from fas.util import _
from fas.models.group import GroupStatus
from fas.models import provider as provider


def get_username_list():
    return provider.get_people()


class EditGroupTypeForm(Form):
    """ Form to edit and validate group type 's informations"""
    name = StringField(_(u'Name'), [validators.Required()])
    comment = StringField(_(u'Description'), [validators.Required()])


class EditGroupStatusForm(Form):
    """ Form to edit and validate group's status"""
    status = SelectField(_(u'Status'),
        [validators.Required()],
        coerce=int,
        choices=[(e.value, e.name.lower()) for e in GroupStatus])


class EditGroupForm(Form):
    """ Form to edit and validate group\'s informations."""
    name = StringField(_(u'Name'), [validators.DataRequired()])
    display_name = StringField(_(u'Display name'), [validators.Required()])
    description = StringField(_(u'Description'), [validators.Optional()])
    web_link = StringField(_(u'Web page'))
    mailing_list = StringField(_(u'Mailing list'))
    mailing_list_url = StringField(_(u'Mailing list URL'))
    irc_channel = StringField(_(u'IRC Channel'))
    irc_network = StringField(_(u'IRC network'))
    # This is using QuerySelectField plugin, commented out for now as not
    # working as expected, using built-in feature.
    # owner_id = QuerySelectField(_(u'Principal Adminn'),
    #    query_factory=get_username_list,
    #    allow_blank=True, blank_text=_(u'-- Select a username --'))
    owner_id = SelectField(
        _(u'Principal Admin'),
        [validators.Required()],
        coerce=int,
        choices=[(-1, _(u'-- None --'))]
    )
    # We want group_type choices list to be dynamic so we won't add it here.
    group_type = SelectField(
        _(u'Group type'),
        [validators.Required()],
        coerce=int,
        choices=[(-1, _(u'-- None --'))])
    # We want parent_group choices list to be dynamic so we won't add it here.
    parent_group_id = SelectField(
        _(u'Parent group'),
        coerce=int,
        choices=[(-1, _(u'-- None --'))])
    private = BooleanField(
        _(u'This group is private'),
        [validators.Optional()],
        default=False)
    self_removal = BooleanField(_(u'Self removal'), default=True)
    need_approval = BooleanField(_(u'Requires approval'), default=False)
    requires_sponsorship = BooleanField(_(u'Requires sponsorship'), default=False)
    requires_ssh = BooleanField(_(u'Requires SSH'), default=False)
    invite_only = BooleanField(_(u'Invite only'), default=False)
    join_msg = TextAreaField(_(u'Join message'))
    apply_rules = TextAreaField(_(u'Apply rules message'))
    bound_to_github = BooleanField(
        _(u'Bind your group to our GitHub oraganization'))
    certificate = SelectField(
        _(u'Attach a certificate to this group'),
        coerce=int,
        choices=[(-1, _(u'-- None --'))])
    license_id = SelectField(
        _(u'License requirement'),
        [validators.Optional()],
        coerce=int)

    def __init__(self, *args, **kwargs):
        super(EditGroupForm, self).__init__(*args, **kwargs)
        # Initialize choices here so we load this every time instead of
        # upon startup
        self.license_id.choices = [
            (l.id, l.name)
            for l in provider.get_licenses()
        ]


class GroupAdminsForm(Form):
    """ Form to select valid group admin. """
    owner_id = SelectField(
        _(u'New principal admin'),
        [validators.Required()],
        coerce=int,
        choices=[(-1, _(u'-- None --'))])


class GroupListForm(Form):
    """ Form to select valid group name. """
    id = SelectField(
        _(u'Select a group'),
        [validators.Required()],
        coerce=int,
        choices=[(-1, _(u'-- None --'))])


class GroupTypeListForm(Form):
    """ Form to select valid group name. """
    id = SelectField(
        _(u'Select a group type'),
        [validators.Required()],
        coerce=int,
        choices=[(-1, _(u'-- None --'))])
