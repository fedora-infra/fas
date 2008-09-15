# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou All rights reserved.
# Copyright © 2008 Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
#            Yaakov Nemoy <ynemoy@redhat.com>
#
import turbogears
from turbogears import controllers, expose

class Help(controllers.Controller):
    help = dict(none=[_('Error'), _('<p>We could not find that help item</p>')],
                show_name=[_('Show Name'), _('''<p>A short name to identify the show, perhaps a code name. Include a date or unique number.</p>''')],
                show_display_name=[_('Show Display Name'), _('''<p>A longer user readable name to describe the show. Preferably the canonical name provided by the event organizers</p>''')],
                show_owner=[_('Show Owner'), _('''<p>The user name of the owner of the event</p>''')],
                group=[_('Show Group'),_('''<p>The name of the group of the participants in the event</p>''')],
                description=[_('Description'), _('''<p>Be descriptive</p>''')])

    def __init__(self):
        '''Create a JsonRequest Controller.'''

    @expose(template="fas.templates.help")
    def get_help(self, helpid='none'):
        try:
            helpItem = self.help[helpid]
        except KeyError:
            return dict(title=_('Error'), helpItem=[_('Error'), _('<p>We could not find that help item</p>')])
        return dict(help=helpItem)
