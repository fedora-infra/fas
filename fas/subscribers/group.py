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
from fas.util import Config, get_data_changes
from fas.events import GroupEdited, GroupCreated, NotificationRequest
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
    request = event.request
    person = event.person
    group = event.group
    form = event.form
    people = group.owner.fullname

    changes = get_data_changes(form, group)

    recipient = group.owner.email

    if group.mailing_list:
        log.debug(
            'Found mailing address %s for group %s, set it up as recipient.'
            % (group.mailing_list, group.name))
        recipient = group.mailing_list

    request.registry.notify(NotificationRequest(
        request=request,
        topic='group.update',
        people=people,
        person=person,
        group=group,
        admin=Config.get('project.admin.email'),
        infos=changes,
        url=event.request.route_url('group-details', id=group.id),
        template='group_update',
        target_email=recipient
    ))

