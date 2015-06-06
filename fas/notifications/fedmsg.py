# -*- coding: utf-8 -*-
#
# Copyright © 2015 Xavier Lamien.
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
from fas.events import NotificationRequest
from fas import log


@subscriber(NotificationRequest)
def on_notification_request(event):
    """
    Sends out notification messages to Fedora messages bus
    on notification's request.
    """
    topic = event.topic
    target = event.fields['people']
    msg = {'agent': target.username}

    if topic.startswith('user.'):
        msg['user'] = target.username
    elif topic.startswith('group.'):
        msg['group'] = event.fields['group'].name
    elif topic.endswith('.update'):
        msg['change'] = event.fields['infos']

    try:
        import fedmsg

        # fedmsg_config = fedmsg.config.load_config()
        # fedmsg.init(**fedmsg_config)
        fedmsg.publish(topic, msg)
    except Exception, e:
        log.warn(str(e))