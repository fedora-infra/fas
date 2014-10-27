# -*- coding: utf-8 -*-

import pyramid.threadlocal

from pyramid.i18n import TranslationStringFactory

from math import ceil

_ = TranslationStringFactory('fas')


class Config():

    @classmethod
    def get(self, configname, default_config=None):
        """ Retrieve config from configuration file.

        :arg configname: string, configuration key to look for
        :return: value of requested configuration.
        """
        registry = pyramid.threadlocal.get_current_registry()
        settings = registry.settings

        return settings[configname] or default_config

    @classmethod
    def get_admin_group(self):
        """ Retrieve admin's group from configuration file."""
        return self.get('project.admin')

    @classmethod
    def get_modo_group(self):
        """ Retrieve moderator's group from configuration file."""
        return self.get('project.moderator')

    @classmethod
    def get_group_editor(self):
        """ Retrieve groups' editor group from configuration file."""
        return self.get('project.group.admin')


def compute_list_pages_from(count, limit=50):
    """ Compute list's pages from given object.

    :arg count: the total number of items in the list
    :arg limit: integer, limt object to compute pages from.
    :return: integer of nb pages.
    """

    return (int(ceil(float(count) / float(limit))), int(count))
