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
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from pyramid.events import subscriber

from fas import log
from fas.util import _
from fas.util import Config, get_data_changes
from fas.notifications.email import Email
from fas.events import GroupEdited, GroupCreated
from fas.lib.fgithub import Github


@subscriber(GroupCreated)
def on_group_created(event):
    """
    Base group creation listener.

    :param event: Pyramid event object
    :type event: pyramid.events
    """
    group = event.group

    if group.bound_to_github:
        gh = Github(log)
        gh.create_group(name=group.name, repo=group.name, access='push')

        # TODO: Add email notification


@subscriber(GroupEdited)
def on_group_edited(event):
    """ Group editing listener. """
    person = event.person
    group = event.group
    form = event.form
    people = group.owner.fullname
    send_email = True

    if person.id == group.owner_id and group.mailing_list is None:
        send_email = False

    changes = get_data_changes(form, group)

    email = Email('group_update')
    recipient = group.owner.email

    if group.mailing_list:
        log.debug(
            'Found mailing address %s for group %s, set it up as recipient.'
            % (group.mailing_list, group.name))
        recipient = group.mailing_list
        people = _(u'folks')
        send_email = True

    email.set_msg(
        topic='updated',
        people=people,
        person=person,
        group=group,
        admin=Config.get('project.admin.email'),
        infos=changes,
        url=event.request.route_url('group-details', id=group.id))

    if send_email and email.is_ready:
        email.send(recipient)
