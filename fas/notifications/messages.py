# -*- coding: utf-8 -*-

from fas.utils import _
from fas.utils import Config

__orga__ = Config.get('project.organisation')
__signature__ = u"""
Regards,
-
The %s
""" % __orga__

membership_msgs = {

    'application': {
        'subject': _(u"""\
        Your membership request for %(groupname)s is being reviewed"""),
        'body': _(u"""\
Hello %(fullname)s,

Your request to be part of group %(groupname)s has been successfully
registered and will be review for approval as soon as possible by
an sponsor or administrator.

You can check your request status by visiting %(url)s.

%(sig)
"""),
        'fields': lambda x, y, z: {
            'fullname': unicode(x.fullname),
            'groupname': unicode(y.name),
            'url': z,
            'sig': __signature__
            }
        },

    'join': {
        'subject': _(u"""Welcome to group %(groupname)s!"""),
        'body': _(u"""\
Hello %(fullname)s,

Thank you for joining group %(groupname)s.

Review your membership at %(url)s

%(sig)s
"""),
        'fields': lambda x, y, z: {
            'fullname': unicode(x.fullname),
            'groupname': unicode(y.name),
            'url': z,
            'sig': __signature__
            }
        },

    'upgrade': {
        'subject': _(u"""You have been upgraded to %(role)s in %(groupname)s"""),
        'body': _(u"""\
Congratulation %(fullname)s,

You have been upgraded to %(role)s into group %(groupname)s.
To review your new role and power visit %(url)s

%(sig)s
"""),
        'fields': lambda x, y, z: {
            'fullname': unicode(x.fullname),
            'groupname': unicode(y.group.name),
            'role': unicode(y.role.name.lower()),
            'url': z,
            'sig': __signature__
            }
        },

    'downgrade': {
        'subject': _(u"""\
You have been downgraded to %(role)s in %(groupname)s"""),
        'body': _(u"""\
Hello %(fullname)s,

this is to inform you that you have been downgraded to %(role)s
into group %(groupname)s.

%(sig)s
"""),
        'fields': lambda x, y: {
            'fullname': unicode(x.fullname),
            'groupname': unicode(y.group.name),
            'role': unicode(y.role.name.lower()),
            'sig': __signature__
            }
    },

    'admin_change': {
        'subject': _(u"""\
Your are now the new %(group)s principal administrator"""),
        'body': _(u"""\
Hello %(fullname)s,

%(former_admin)s has made you the new principal administrator for group
%(groupname)s.

Review your new group information at %(url)s

%(sig)s
"""),
        'fields': lambda w, x, y, z: {
            'fullname': unicode(w.fullname),
            'groupname': unicode(x.name),
            'former_admin': y,
            'url': z,
            'sig': __signature__
            }
    },

    'revoke': {
        'subject': _(u"""You have been removed from group %(groupname)s"""),
        'body_self_removal': _(u"""\
This is to inform you that you have been successfully removed from the
%(groupname)s group as requested.

%(sig)s
"""),
        'body_admin_revoked': _(u"""\
This is to inform you that you have been removed from the group %(groupname)s
with the following reason:

%(reason)s

If you believe this action is not expected to be happened please, contact
an group's administrator or an account's administrator.

%(sig)s
"""),
        'fields': lambda x, y, z: {
            'fullname': unicode(x.fullname),
            'groupname': unicode(y.name),
            'reason': z,
            'sig': __signature__
            }
        },
}