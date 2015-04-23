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

from fas.util import Config
from fas.lib.mailer import send_email

from messages import Msg

import logging

log = logging.getLogger(__name__)


class Email(object):

    def __init__(self, template):
        self.subject = ""
        self.body = ""
        self.is_ready = False
        tplt = getattr(Msg(Config), template)
        self.msg = tplt()

    def __set_is_ready__(self, ready=False):
        """ Set email objects as ready to be sent."""
        self.is_ready = ready

    def is_ready(self):
        """
        Returns True if email object is ready or not to send out its contents.
        """
        return self.is_ready

    def send(self, recipient=None):
        """ Send out predefined emails. """
        if recipient is not None:
            send_email(
                message=self.body,
                subject=self.subject,
                mail_to=recipient,
                logger=log
                )
            self.__set_is_ready__(False)

    def set_msg(self, topic, subject='subject', body='body', **fields):
            """ Set up message from given template."""
            self.__set_is_ready__(True)

            self.subject = self.msg[topic][subject]\
            % self.msg[topic]['fields'](**fields)
            self.body = self.msg[topic][body]\
            % self.msg[topic]['fields'](**fields)

            if not isinstance(self.subject, basestring)\
            and not isinstance(self.body, basestring):
                self.__set_is_ready__(False)
