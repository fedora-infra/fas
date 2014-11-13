# -*- coding: utf-8 -*-


class Msg(object):

    def __init__(self, config):
        self.config = config

    def signature(self):
        return u"""\
Regards,
-
The %(orga)s
""" % {'orga': self.config.get('project.organisation')}

    def membership_update(self):
        return {

    'application': {
        'subject': u"""\
        Your membership request for %(groupname)s is being reviewed""",
        'body': u"""\
Hello %(fullname)s,

Your request to be part of group %(groupname)s has been successfully
registered and will be review for approval as soon as possible by
an sponsor or administrator.

You can check your request status by visiting %(url)s.

%(sig)
""",
        'fields': lambda **x: {
            'fullname': unicode(x['people'].fullname),
            'groupname': unicode(x['group'].name),
            'url': x['url'],
            'sig': self.signature()
            }
        },

    'join': {
        'subject': u"""Welcome to group %(groupname)s!""",
        'body': u"""\
Hello %(fullname)s,

Thank you for joining group %(groupname)s.

Review your membership at %(url)s

%(sig)s
""",
        'fields': lambda **x: {
            'fullname': unicode(x['people'].fullname),
            'groupname': unicode(x['group'].name),
            'url': x['url'],
            'sig': self.signature()
            }
        },

    'upgrade': {
        'subject': u"""\
        You have been promoted to %(role)s in group %(groupname)s""",
        'body': u"""\
Congratulation %(fullname)s,

You have been upgraded to %(role)s into group %(groupname)s.
To review your new role and power visit %(url)s

%(sig)s
""",
        'fields': lambda **x: {
            'fullname': unicode(x['people'].fullname),
            'groupname': unicode(x['group'].name),
            'role': unicode(x['role'].name.lower()),
            'url': x['url'],
            'sig': self.signature()
            }
        },

    'downgrade': {
        'subject': u"""\
You have been demoted to %(role)s in group %(groupname)s""",
        'body': u"""\
Hello %(fullname)s,

this is to inform you that you have been downgraded to %(role)s
into group %(groupname)s.

%(sig)s
""",
        'fields': lambda **x: {
            'fullname': unicode(x['people'].fullname),
            'groupname': unicode(x['group'].name),
            'role': x['role'].name.lower(),
            'sig': self.signature()
            }
    },

    'admin_change': {
        'subject': u"""\
Your have been promoted as the new principal administrator of %(groupname)s""",
        'body': u"""\
Hello %(fullname)s,

%(former_admin)s has made you the new principal administrator for group
%(groupname)s.

Review your new group information at %(url)s

%(sig)s
""",
        'fields': lambda **x: {
            'fullname': unicode(x['people'].fullname),
            'groupname': unicode(x['group'].name),
            'former_admin': x['admin'].fullname,
            'url': x['url'],
            'sig': self.signature()
            }
    },

    'revoke': {
        'subject': u"""You have been removed from group %(groupname)s""",
        'body_self_removal': u"""\
Hello %(fullname)s,

This is to inform you that you have been successfully removed from the
%(groupname)s group as requested.

%(sig)s
""",
        'body_admin_revoked': u'''\
Hello %(fullname)s,

This is to inform you that you have been removed from the group %(groupname)s
with the following reason:

%(reason)s

If you believe this action is not expected to be happened please, contact
an group\'s administrator or an account\'s administrator.

%(sig)s
''',
        'fields': lambda **x: {
            'fullname': unicode(x['people'].fullname),
            'groupname': unicode(x['group'].name),
            'reason': x['reason'],
            'sig': self.signature()
            }
            },
        }