# -*- coding: utf-8 -*-

from fas.utils import Config
from fas.utils.notify import send_email

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
