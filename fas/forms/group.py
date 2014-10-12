# -*- coding: utf-8 -*-

from wtforms import (
    Form,
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    validators
    )

#from wtforms.ext.sqlalchemy.fields import QuerySelectField

from fas.utils import _
from fas.models import provider as provider

def get_username_list():
    return provider.get_people()


class EditGroupTypeForm(Form):
    """ Form to edit and validate group type 's informations"""
    name = StringField(_(u'Name'), [validators.Required()])
    comment = StringField(_(u'Description'), [validators.Required()])


class EditGroupForm(Form):
    """ Form to edit and validate group\'s informations."""
    name = StringField(_(u'Name'))
    display_name = StringField(_(u'Display name'), [validators.Required()])
    description = StringField(_(u'Description'), [validators.Optional()])
    web_link = StringField(_(u'Web page'))
    mailing_list = StringField(_(u'Mailing list'))
    mailing_list_url = StringField(_(u'Mailing list URL'))
    irc_channel = StringField(_(u'IRC Channel'))
    irc_network = StringField(_(u'IRC network'))
    # This is using QuerySelectField plugin, commented out for now as not working
    # as expected, using built-in feature.
    #owner_id = QuerySelectField(_(u'Principal Adminn'),
    #    query_factory=get_username_list,
    #    allow_blank=True, blank_text=_(u'-- Select a username --'))
    owner_id = SelectField(_(u'Principal Admin'),
        [validators.Required()],
        coerce=int,
        choices=[(u.id, u.username + ' (' + u.fullname + ')')
            for u in provider.get_people()])
    # We want group_type choices list to be dynamic so we won't add it here.
    group_type = SelectField(_(u'Group type'),
        [validators.Required()],
        coerce=int,
        choices=[(-1, _(u'-- None --'))])
        #choices=[(t.id, t.name) for t in provider.get_group_types()])
    # We want parent_group choices list to be dynamic so we won't add it here.
    parent_group_id = SelectField(_(u'Parent group'),
        coerce=int,
        choices=[(-1, _(u'-- None --'))])
    private = BooleanField(_(u'This group is private'),
        [validators.Optional()],
        default=False)
    self_removal = BooleanField(_(u'Self removal'),
        default=True)
    need_approval = BooleanField(_(u'Requires approval'),
        default=True)
    invite_only = BooleanField(_(u'Invite only'))
    join_msg = TextAreaField(_(u'Join message'))
    apply_rules = TextAreaField(_(u'Apply rules message'))
    bound_to_github = BooleanField(_(u'Bind your group to our GitHub oraganization'))
    license_sign_up = SelectField(_(u'License requirement'),
        [validators.Optional()],
        coerce=int,
        choices=[(l.id, l.name) for l in provider.get_licenses()])
