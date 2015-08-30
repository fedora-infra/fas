# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Xavier Lamien.
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

from fas.util import _


class Msg(object):
    def __init__(self, config):
        self.config = config

    def signature(self):
        """ Email signature template. """
        sig = _(u'''\
Regards,
-
The %(orga)s
''' % {'orga': self.config.get('project.organisation')})
        return sig

    def account_update(self):
        """ Account messages template. """
        return {
            'user.registration': {
                'subject': u"""Confirm your %(organisation)s Account!""",
                'body': u"""\
Welcome to the %(organisation)s!

You are just one step away from contributing to a great FOSS community!

To complete your account creation, please visit this link:
%(url)s

%(sig)s
""",
                'fields': lambda **x: {
                    'organisation': x['organisation'],
                    'url': x['url'],
                    'sig': self.signature()
                }
            },
            'user.password.reset': {
                'subject': u"""Password reset request on your account""",
                'body': u"""\
Hello %(fullname)s,

Someone (hopefully you) has requested a password reset for your account
`%(username)s` on the %(organisation)s Account System (FAS): %(url)s.

To complete this procedure, please visit this link:
%(validation_url)s

If you did not request this password change, simply disregard this email and
please contact a FAS administrator %(admin_email)s.
This email is sent only to the address on file for your account and will become
invalid after 24 hours.

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': x['people'].fullname,
                    'username': x['people'].username,
                    'organisation': x['organisation'],
                    'url': self.config.get('project.url'),
                    'validation_url': x['reset_url'],
                    'admin_email': self.config.get('project.admin.email'),
                    'sig': self.signature()
                }
            },
            'user.password.update': {
                'subject': u"""Account password change confirmation""",
                'body': u"""\
Hello %(fullname)s,

This email confirms that you have successfully changed your password
for account %(username)s.

If you did not initiate this password change, please contact a FAS
administrator immediately %(admin_email)s.

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': x['people'].fullname,
                    'username': x['people'].username,
                    'admin_email': self.config.get('project.admin.email'),
                    'sig': self.signature()
                }
            },
            'user.update': {
                'subject': u"""Account information update for %(username)s""",
                'body': u"""\
Hello %(fullname)s,

Someone (hopefully you) has changed your FAS account information.
if these changes are not expected, please contact a FAS administrator
%(admin)s and let them know.

Updated information:

%(infos)s


To review the changes, please log in at: %(url)s

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': x['people'].fullname,
                    'username': x['people'].username,
                    'admin': x['admin'],
                    'infos': x['infos'],
                    'url': x['url'],
                    'sig': self.signature()
                }
            }
        }

    def group_update(self):
        """ Group messages template. """
        return {
            'group.new': {
                'subject': u"""A new FAS Group has been created %(groupname)s""",
                'body': u"""\
Hello admins,

%(person)s has just created a new group.

Name: %(groupname)s
Principal admin: %(groupadmin)s
Type: %(grouptype)s

%(description)s

To review full group's information, please visit %(url)s

%(sig)s
""",
                'fields': lambda **x: {
                    'groupname': x['group'].name,
                    'groupadmin': x['group'].owner.username,
                    'grouptype': x['group'].group_types.name,
                    'description': x['group'].description,
                    'person': x['person'].username,
                    'url': x['url'],
                    'sig': self.signature()
                }
            },

            'group.update': {
                'subject': u"""Group update %(groupname)s""",
                'body': u"""\
Hello group's admin(s),

%(person)s has just updated information about group %(groupname)s.
If these changes are not expected please, contact %(admin)s and let them know.

Updated information:

%(infos)s


If the above information is incorrect, please log in and fix it at:
    %(url)s

%(sig)s
""",
                'fields': lambda **x: {
                    'groupname': x['group'].name,
                    'person': x['person'].fullname,
                    'admin': x['admin'],
                    'infos': x['infos'],
                    'url': x['url'],
                    'sig': self.signature()
                }
            },

            'group.delete': {
                'subject': u"""Group %(groupname)s has been deleted!""",
                'body': u"""
Hello admins,

%(person)s has just deleted group %(groupname)s.

Note that any related membership to this group has been revoked,
including all synchronized clients access's.

%(sig)s
""",
                'fields': lambda **x: {
                    'groupname': x['group'].name,
                    'person': x['person'].username,
                    'sig': self.signature()
                }
            }
        }

    def membership_update(self):
        """ Group membership messages template."""
        return {
            'group.invite': {
                'subject': u"""\
Invitation to join %(orga)s group %(groupname)s!""",
                'body': u"""\
%(fullname)s has invited you to join the %(orga)s by joining the group %(groupname)s!

We are a community of users and developers who produce a complete
operating system from entirely free and open source software (FOSS).

%(fullname)s thinks that you have knowledge and skills that make you a great fit
for the Fedora community, and that you might be interested in contributing.

How could you team up with the Fedora community to use and develop your skills?
Check out http://fedoraproject.org/join-fedora for some ideas.

Our community is more than just software developers
Fedora and FOSS are changing the world, come be a part of it!

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': x['people'].fullname,
                    'groupname': x['group'].name,
                    'url': x['url'],
                    'orga': x['organisation'],
                    'sig': self.signature()
                }
            },

            'group.member.apply': {
                'subject': u"""Your membership request for %(groupname)s""",
                'body': u"""\
Hello %(fullname)s,

Your request to join group %(groupname)s has been successfully
registered and will be review for approval as soon as possible by
an sponsor or administrator.

You can check your request status by visiting %(url)s.

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': x['people'].fullname,
                    'groupname': x['group'].name,
                    'url': x['url'],
                    'sig': self.signature()
                }
            },

            'group.member.approve': {
                'subject': u"""\
Your membership request for %(groupname)s has been approved""",
                'body': u"""\
Hello %(fullname)s,

%(sponsor)s has approved your request and will be sponsoring you
into group %(groupname)s.

For more details on your new membership, visit this link %(url)s

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': unicode(x['people'].fullname),
                    'groupname': x['group'].name,
                    'sponsor': unicode(x['sponsor'].fullname),
                    'url': x['url'],
                    'sig': self.signature()
                }
            },

            'group.join': {
                'subject': u"""Welcome to group %(groupname)s\!""",
                'body': u"""\
Hello %(fullname)s,

Thank you for joining group %(groupname)s.

Review your membership at %(url)s

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': unicode(x['people'].fullname),
                    'groupname': x['group'].name,
                    'url': x['url'],
                    'sig': self.signature()
                }
            },

            'group.member.role.upgrade': {
                'subject': u"""\
You have been promoted to %(role)s in group %(groupname)s""",
                'body': u"""\
Congratulation %(fullname)s,

%(sponsor)s has promoted you to %(role)s into group %(groupname)s.
To review your new role and power visit %(url)s

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': unicode(x['people'].fullname),
                    'groupname': unicode(x['group'].name),
                    'role': unicode(x['role'].name.lower()),
                    'sponsor': unicode(x['sponsor'].fullname),
                    'url': x['url'],
                    'sig': self.signature()
                }
            },

            'group.member.role.downgrade': {
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

            'group.admin_change': {
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

            'group.member.revoke': {
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

    def certificate(self):
        """ New client certificate message template. """
        return {
            'new_client_cert': {
                'subject': u"""\
Your new certificate has been generated for group %(groupname)s!""",
                'body': u"""\
Hello %(fullname)s,

You have generated a new SSL client certificate. If you did not request this,
please contact %(admin_email)s and let them know.

Note that certificate generated prior to the current one have been
automatically revoked, and should stop working within the hour.

%(sig)s
""",
                'fields': lambda **x: {
                    'fullname': unicode(x['people'].fullname),
                    'groupname': unicode(x['group']),
                    'admin_email': self.config.get('project.admin.email'),
                    'sig': self.signature()
                }
            },
        }

