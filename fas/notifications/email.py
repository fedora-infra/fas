# -*- coding: utf-8 -*-

from fas.utils import _
from fas.utils.notify import send_email

from fas.models import AccountLogType

from .messages import membership_msgs as msg


class Email(object):

    def __init__(self, recipient=None):
        self.subject = ""
        self.body = ""
        self.recipient = recipient
        self.is_ready = False

    def __set_is_ready__(self, ready=False):
        """ Set email objects as ready to be sent."""
        self.is_ready = ready

    def is_ready(self):
        """ Tell if email object is ready or not to send out its contents."""
        return self.is_ready

    def send(self):
        """ Send out email with pre-configured email contents."""
        if self.recipient is not None:
            send_email(
                message=self.body,
                subject=self.subject,
                mail_to=self.recipient
                )

    def set_revoked_membership(self, people, group, reason=None, eta=None):
        """ Notify about given person about its membership revoking. """
        if reason is None:
            reason = ""

        fields = msg['revoke']['fields'](people, group, reason)

        if eta == AccountLogType.REVOKED_GROUP_MEMBERSHIP:
            self.body = msg['revoke']['body_self_removal'] % fields

        elif eta == AccountLogType.REVOKED_GROUP_MEMBERSHIP_BY_ADMIN:
            self.body = msg['revoke']['body_admin_revoked'] % fields

        self.__set_is_ready__(True)