# -*- coding: utf-8 -*-
#
# Copyright © 2014 Xavier Lamien.
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

from socket import error as socket_error
from pyramid.events import subscriber

from fas.events import NotificationRequest
from fas.util import Config, _
from fas.lib.mailer import send_email
from fas.notifications.messages import Msg
from fas import log


@subscriber(NotificationRequest)
def on_notification_request(event):
    """
    Sends out email's notification on notification's request.
    """
    topic = event.topic
    subject = event.subject
    body = event.body
    fields = event.fields

    if 'target_email' in fields:
        recipient = fields['target_email']
    else:
        recipient = fields['people'].email

    tplt = getattr(Msg(Config), fields['template'])
    msg = tplt()

    # TODO: Add related error msg to message template.
    error_msg = 'We are having trouble sending...'

    subject = msg[topic][subject] % msg[topic]['fields'](**fields)
    body = msg[topic][body] % msg[topic]['fields'](**fields)

    if body is not None and isinstance(body, unicode):
        try:
            send_email(
                message=body,
                subject=subject,
                mail_to=recipient,
                logger=log)
        except socket_error, e:
            log.error('Unable to send email: %s', str(e))
            event.request.flash(_('%s' % error_msg))
    else:
        log.warn('Unable to send out email, could not found email message.')