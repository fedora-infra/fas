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

import datetime
import logging

from pyramid.events import subscriber

from fas.events import PasswordChangeRequested, PeopleInfosUpdated, \
    NotificationRequest, LoginSucceeded
from fas.events import NewUserRegistered
from fas.util import Config, get_data_changes, _
from fas.views import redirect_to

log = logging.getLogger(__name__)


@subscriber(PasswordChangeRequested)
def on_password_change_requested(event):
    """ Check that user is allowed to get through. """
    person = event.person
    curr_dtime = datetime.datetime.utcnow()
    last_dtime = person.last_logged
    delta = (curr_dtime - last_dtime).seconds

    log.debug('Checking current time %s against last login\'s time %s' %
              (curr_dtime, last_dtime))

    if delta >= int(Config.get('user.security_change.timeout')):
        log.debug('Too many time passed since last login, ask user to '
                  're-enter its password')
        raise redirect_to('/login?redirect=%s' % event.request.url)
    else:
        log.debug('last login time still valid')


@subscriber(NewUserRegistered)
def on_new_user_registered(event):
    """ New user signup listener. """
    request = event.request
    person = event.person

    request.registry.notify(NotificationRequest(
        request=request,
        topic='user.registration',
        organisation=Config.get('project.organisation'),
        url=request.route_url(
            'people-confirm-account',
            username=person.username,
            token=person.password_token),
        template='account_update'
    ))


@subscriber(PeopleInfosUpdated)
def on_people_updated(event):
    """
    Default People info update listener.
    Retrieves updated data and request notification.
    """
    request = event.request
    person = event.person

    changes = get_data_changes(event.form, person, keep_value=False)

    request.registry.notify(NotificationRequest(
        request=request,
        topic='user.update',
        admin=Config.get('project.admin.email'),
        people=person,
        infos=changes,
        url=event.request.route_url('people-profile', id=person.id),
        template='account_update'
    ))


@subscriber(LoginSucceeded)
def check_ssh_key(event):
    """
    Checks and notifies - with a flash msg - authenticated user that an SSH key
    is required if none have been set up.

    :param event: pyramid event
    :type event: pyramid.events
    """
    person = event.person

    ssh_is_required = False
    for m in person.group_membership:
        if m.group and m.group.requires_ssh:
            ssh_is_required = True

    if not person.ssh_key and ssh_is_required:
        event.request.session.flash(_(u'One of the group you belong to '
                                      u'requires an SSH key.\n'
                                      u'Go to your profile to add one.'),
                                    'warning')
