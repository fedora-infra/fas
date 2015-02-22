# -*- coding: utf-8 -*-

import pyramid.threadlocal
import datetime

from babel.dates import format_date, format_time

from pyramid.i18n import TranslationStringFactory

from math import ceil

_ = TranslationStringFactory('fas')


class Config():

    def __init__(self):
        pass

    @classmethod
    def get(self, configname, default_config=None):
        """ Retrieve config from configuration file.

        :param configname: configuration key to look for
        :type configname: str
        :param default_config: default config value to use if config not found
        :type default_config: str|int|list|unicode
        :return: value of requested configuration key.
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

    :param count: Total number of items in the list
    :type count: int
    :param limit: integer, limit object to compute pages from.
    :type limit: int
    :return: number of pages.
    :rtype: int
    """
    if limit <= 0:
        return int(count)

    return int(ceil(float(count) / float(limit)))


def locale_negotiator(request):
    """ Manage [dynamically] locale on request. """
    if request.get_user:
        return request.get_user.locale

    return str(Config.get('locale.default'))


def format_datetime(locale, tdatetime):
        """ format given `datetime` in a translated human-readable format.

        :param locale: locale to format from
        :type locale: str
        :param tdatetime: datetime to format from
        :type tdatetime: datetime.datetime
        :rtype: str | unicode
        """
        current_date = datetime.datetime.utcnow().date()
        date = tdatetime.date()
        time = tdatetime.time()

        if date == current_date:
            tdatetime = format_time(time, locale=locale)
        else:
            tdatetime = format_date(date, locale=locale)

        return tdatetime


# Originally from http://stackoverflow.com/a/23705687/1106202
class UTC(datetime.tzinfo):
    def tzname(self):
        return "UTC"

    def utcoffset(self, dt):
        return datetime.timedelta(0)


def utc_iso_format(utc):
    """
    Python's built in isoformat method for UTC datetime objects is,
    despite its name, not really ISO format. It breaks the specification which
    requires that if there is no timezone suffix, the time should be considered
    local (not UTC) time. By default, datetime objects don't carry any timezone
    information at all. So, here we format it ourselves to format it in the
    right way, but we have no guarantee that the thing passed is actually a
    *UTC* time as opposed to a local time, so this could very easily generate
    bad output. In a typed environment this issue would be eliminated.

    This change, as long as it's only applied to actual UTC times, results in
    being able to parse the time correctly in environments which do follow the
    specification.

    :param utc: datetime in UTC format
    :type utc: datetime.datetime
    :rtype: datetime.datetime.isoformat
    """
    return utc.replace(tzinfo=UTC()).isoformat()
