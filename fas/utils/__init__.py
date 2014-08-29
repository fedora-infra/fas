# -*- coding: utf-8 -*-

import pyramid.threadlocal

from pyramid.i18n import TranslationStringFactory

from fas.models import provider as provider

from math import ceil

_ = TranslationStringFactory('fas')


class Config():

    @classmethod
    def get(self, configname):
        """ Retrieve config from configuration file.

        :arg configname: string, configuration key to look for
        :return: value of requested configuration.
        """
        registry = pyramid.threadlocal.get_current_registry()
        settings = registry.settings

        return settings[configname]

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


def compute_list_pages_from(str_obj, limit=50):
    """ Compute list's pages from given object.

    :arg obj: string, object to compute pages from.
    :arg limit: integer, limt object to compute pages from.
    :return: integer of nb pages.
    """
    count = getattr(provider, 'get_%s_count' % str_obj)
    count = count()

    return (int(ceil(float(count) / float(limit))), int(count))