# -*- coding: utf-8 -*-


from github import Github
from github import UnknownObjectException, GithubException
from fas.utils import Config


class Github(Github):

    def __init__(self):
        super(Github, self).__init__(
            Config.get('github.token'),
            user_agent=Config.get('project.name') + "\FAS 3.0")
        # self.enable_console_debug_logging()
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
        msg = None
        repo = []

        try:
            group = self.org.create_team(
                name=name, repo_names=repo, permission=access)
        except UnknownObjectException:
            msg = group
        except GithubException:
            msg = group

        return (group, msg)
