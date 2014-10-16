# -*- coding: utf-8 -*-

import random
import string

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


def compute_list_pages_from(count, limit=50):
    """ Compute list's pages from given object.

    :arg count: the total number of items in the list
    :arg limit: integer, limt object to compute pages from.
    :return: integer of nb pages.
    """

    return (int(ceil(float(count) / float(limit))), int(count))


def generate_token(size=15, chars=string.ascii_uppercase + string.digits):
    """ Generates a random identifier for the given size and using the
    specified characters.
    If no size is specified, it uses 15 as default.
    If no characters are specified, it uses ascii char upper case and
    digits.

    :arg size: the size of the identifier to return.
    :arg chars: the list of characters that can be used in the
        idenfitier.
    """
    return ''.join(random.choice(chars) for x in range(size))
