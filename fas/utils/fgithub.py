# -*- coding: utf-8 -*-

import logging
from logging import Logger

from github import Github
from github import UnknownObjectException, GithubException, enable_console_debug_logging
from fas.utils import Config


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

    def create_group(self, name, repo=[], access='pull'):
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
