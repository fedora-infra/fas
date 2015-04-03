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

from fas.events import LoginFailed
from fas.events import LoginRequested
from fas.events import LoginSucceeded

from fas.utils import _
from fas.utils import Config

from fas.models import AccountStatus
from fas.models import AccountLogType
from fas.models import register
from fas.views import redirect_to

import logging
import datetime

log = logging.getLogger(__name__)


@subscriber(LoginFailed)
def onLoginFailed(event):
    """ Login failure listener. """
    person = event.person

    if person:
        if person.login_attempt is None:
            person.login_attempt = 0
        else:
            if person.login_attempt > int(Config.get('login.failed_attempt')):
                person.status = AccountStatus.LOCKED
                register.add_people(person)
                log.debug(
                    'Account %s locked, number of failure attempt reached: %s' %
                    (person.username, person.login_attempt)
                )

        person.login_attempt += 1

    event.request.session.flash(_('Login failed'), 'login')


@subscriber(LoginRequested)
def onLoginRequested(event):
    """ Login request listener. """
    person = event.person

    if person:
        if person.login_attempt >= int(Config.get('login.failed_attempt')):
            lock_timeout = int(Config.get('login.lock.timeout'))
            unlock_time = person.date_updated + datetime.timedelta(
                0, (60 * lock_timeout))

            if datetime.datetime.utcnow() > unlock_time:
                log.debug(
                    'Lock time passed, unlocking account %s' % person.username)
                person.status = AccountStatus.ACTIVE
                person.login_attempt = 0

                register.add_people(person)
            else:
                log.debug(
                    'Account %s will be unlocked at %s UTC'
                    % (person.username, unlock_time.time())
                )
                event.request.session.flash(
                    _(u'Your account has been locked down due to '
                      u'too many login failure\'s attempt.Account locked for %smin'
                      % lock_timeout), 'error')
                raise redirect_to('/login')


@subscriber(LoginSucceeded)
def onLoginSucceeded(event):
    """ Login success listener. """
    person = event.person
    request = event.request

    if person.login_attempt > 0:
        log.debug(
            'Account %s successfully logged in, resetting failure attempt count.'
            % person.username)
        person.login_attempt = 0
        register.add_people(person)

    person.last_logged = datetime.datetime.utcnow()

    register.save_account_activity(request, person.id, AccountLogType.LOGGED_IN)

