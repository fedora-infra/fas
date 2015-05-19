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

import logging
from logging import Logger

from github import Github
from github import UnknownObjectException, GithubException, enable_console_debug_logging
from fas.util import Config


class Github(Github):

    def __init__(self, logger=None):
        super(Github, self).__init__(
            Config.get('github.token'),
            user_agent=Config.get('github.client.user-agent'))

        if not isinstance(logger, Logger):
            self.log = logging.getLogger()
        else:
            self.log = logger

        if self.log.isEnabledFor(logging.DEBUG):
            enable_console_debug_logging()

        self.org = self.get_organization(Config.get('github.organization'))

    # def get_organization(self):
        # """ Retrieve registered organization.
        # :rtype: string, organiszation name
        # """
        # return self.org.name

    def get_group(self, name):
        """ Retrieve organization's team from given name.

        :param name: string, team name.
        :rtype: string, team name found.
        """
        return self.org.get_team(name)

    def create_group(self, name, repo=None, access='pull'):
        """ Create a new team from registered oraganization.

        :param team: string, a group name for the team.
        :param access: string, granted permission for requested team
        :rtype: tuple of :class:`github.Team.Team` and msg if error happens.
        """
        group = None
        repo = []

        try:
            group = self.org.create_team(
                name=name, repo_names=repo, permission=access)
            self.log.debug('Created team %s' % group)
        except UnknownObjectException, e:
            self.log.debug(e)
        except GithubException, e:
            self.log.error('Something happened when creating team: %s', e)

        if group is not None:
            return True

        return False
