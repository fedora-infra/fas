# -*- coding: utf-8 -*-

from wtforms import (
    Form,
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    validators
    )

from fas.utils import _
from fas.models import provider as provider


class EditGroupForm(Form):
    """ Form to edit and validate group\'s update."""
    name = StringField(_(u'Name'), [validators.Required()])
    display_name = StringField(_(u'Display name'), [validators.Required()])
    web_link = StringField(_(u'Web page'))
    mailing_list = StringField(_(u'Mailing list'))
    mailing_list_url = StringField(_(u'Mailing list URL'))
    irc_channel = StringField(_(u'IRC Channel'))
    irc_network = StringField(_(u'IRC network'))
    owner_id = SelectField(_(u'Group owner'),
        choices=[(name, name) for name in provider.get_people_username()])
    group_type = SelectField(_(u'Group type'),
        choices=[(type, type) for type in provider.get_group_types()])
    parent_group_id = SelectField(_(u'Parent group'),
        choices=[
            (group, group) for group in provider.get_candidate_parent_groups()])
    private = BooleanField(_(u'Private'))
    self_removal = BooleanField(_(u'Self removal'))
    need_approval = BooleanField(_(u'Need aproval'))
    invite_only = BooleanField(_(u'Invite only'))
    join_msg = TextAreaField(_(u'Join message'))
    apply_rules = TextAreaField(_(u'Apply rules message'))
    license_sign_up = SelectField(_(u'License requirement'),
        choices=[(lce, lce) for lce in provider.get_licenses()])
