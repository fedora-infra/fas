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

from fas.events import PasswordChangeRequested, PeopleInfosUpdated
from fas.events import NewUserRegistered

from fas.notifications.email import Email
from fas.utils import Config, get_data_changes
from fas.views import redirect_to

import datetime
import logging

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

    email = Email('account_update')

    email.set_msg(
        topic='registration',
        organisation=Config.get('project.organisation'),
        url=request.route_url(
            'people-confirm-account',
            username=person.username,
            token=person.password_token)
    )

    email.send(person.email)


@subscriber(PeopleInfosUpdated)
def on_people_updated(event):
    """ People infos update listener. """
    person = event.person
    changes = get_data_changes(event.form, person, keep_value=False)

    email = Email('account_update')

    email.set_msg(
        topic='data-update',
        admin=Config.get('project.admin.email'),
        people=person,
        infos=changes,
        url=event.request.route_url('people-profile', id=person.id)
    )
    email.send(person.email)