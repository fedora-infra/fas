# -*- coding: utf-8 -*-

from pyramid.events import subscriber

from fas.events import PasswordChangeRequested
from fas.events import NewUserRegistered

from fas.notifications.email import Email
from fas.utils import Config
from fas.views import redirect_to

import datetime
import logging

log = logging.getLogger(__name__)


@subscriber(PasswordChangeRequested)
def onPasswordChangeRequested(event):
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
def onNewUserRegistered(event):
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

