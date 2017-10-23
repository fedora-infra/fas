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

from pyramid.events import subscriber

from fas.events import GroupBindingRequested

from fas.util import _
from fas.lib.fgithub import Github

import logging

log = logging.getLogger(__name__)


@subscriber(GroupBindingRequested)
def create_gh_team(event):
    """ Create a github team base on group name."""
    group = str(event.form.name.data)
    gh = Github(logger=log)

    if not gh.create_group(name=group, repo=group, access='push'):
        event.form.bound_to_github.data = False
        event.form.populate_obj(event.group)
        event.request.session.flash(
            _(u'Your group cannot be bound to our GitHub organisation\n'
              u'If you keep having this issue please, contact an admin'),
            'error')
    else:
        event.request.session.flash(
            _(u'Group successfully bound to github'), 'info')

