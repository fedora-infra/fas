# -*- coding: utf-8 -*-

from fas.utils import _
from fas.utils import Config
from fas.utils.notify import send_email

from fas.models import AccountLogType


class Notify(object):

    @classmethod
    def revoked_membership(self, people, group, reason=None, eta=None):
        """ Notify about given person about its membership revoking. """
        middle_text = None
        subject = _(
            'You have been removed from the group: %s' %
            group.name)

        if eta == AccountLogType.REVOKED_GROUP_MEMBERSHIP_BY_ADMIN:
            middle_text = _("""
This is to inform you that you have been removed from the %s group
""" % group.name)
            if reason:
                middle_text = middle_text + ("""
with the following reason:

%(reason)s""") % ({'reason': reason})
        elif eta == AccountLogType.REVOKED_GROUP_MEMBERSHIP:
            middle_text = _("""
This is to inform you that you have been successfully removed from the
%(groupname)s group as requested.""") % ({'groupname': group.name})

        text = _("""
Hello %(fullname)s,

%(middle_text)s

If you believe this action is not expected, please, contact
the group's administrator or an %(organisation)s administrator.

Regards,

The %(organisation)s
""" % ({
        'fullname': people.fullname,
        'organisation': Config.get('project.organisation'),
        'groupname': group.name,
        'middle_text': middle_text
    }))

        send_email(message=text, subject=subject, mail_to=people.email)