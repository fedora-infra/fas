# -*- coding: utf-8 -*-

from pyramid.events import subscriber

from fas.events import TokenUsed

import datetime
import logging

log = logging.getLogger(__name__)


@subscriber(TokenUsed)
def on_token_used(event):
    """ Token activity listener. """
    event.perm.last_used = datetime.datetime.utcnow()

    log.debug('Saving token last usage timestamp for user %s',
        event.person.username)

