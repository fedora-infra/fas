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
__author__ = ['Xavier Lamien <laxathom@fedoraproject.org>',
              'Pierre-Yves Chibon <pingou@fedoraproject.org>',
              'Ricky Elrod <ricky@elrod.me>']

import pyramid.threadlocal
import datetime
from webob.multidict import MultiDict
from babel.dates import format_date, format_time

from pyramid.i18n import TranslationStringFactory

from math import ceil

from fas import log

_ = TranslationStringFactory('fas')


class Config(object):
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
        config = None

        try:
            config = settings.get(configname) or default_config
        except TypeError:
            # We might hit this if we call registry too soon when initializing
            pass

        return config

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
        return int(count) or 1

    return int(ceil(float(count) / float(limit))) or 1


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
    if utc is not None:
        return utc.replace(tzinfo=UTC()).isoformat()

    return None


def get_data_changes(form, data, keep_value=True):
    """
    Get data changes from given data and stored one.

    :param form: updated data to diff from
    :param data: current data to diff from
    :return: changes data
    :rtype: basestring
    """
    diff = set(
        k for k in set(
            data.__dict__.keys()
        ).intersection(
            set(form.data.keys()))
        if data.__dict__[k] != form.data[k]
    )
    changes = ''
    for change in diff:
        field = getattr(form, change)
        if keep_value:
            changes += u"""    %s:    %s\n""" % (
                field.label.__dict__['text'], form.data[change]
            )
        else:
            changes += field.label.__dict__['text']

    return changes


def get_reversed_domain_name():
    """
    :return: A reversed domain's name
            'domain.tld' becomes 'tld.domain'
    :rtype: str
    """
    domain = Config.get('project.domain.name', 'fedoraproject.org')

    if domain:
        domain = domain.split('.')
        return '.'.join(domain[::-1])
    else:
        return 'fedora'


def setup_group_form(request, group=None):
    """
    Dynamically setup group info from given active request

    :param request: pyramid request object
    :type request: pyramid.request
    :param group: group object to setup form from
    :type group: str
    :return: populated group form
    :rtype: fas.forms.group.EditGroupForm
    """
    from fas.forms.group import EditGroupForm
    from fas.models import provider as provider

    data = None
    form_data = request.POST

    if 'Content-type' in request.headers:
        if request.headers['Content-Type'] == 'application/json':
            data = request.json_body
        elif data and group:
            # Assuming here we're having an editing request from remote client
            form_data = MultiDict(data)

    form = EditGroupForm(form_data, group, data=data)

    if group is not None:
        # Group's name is not edit-able
        form.name.data = group.name
        # Remove group being edited from parent list if present
        parent_groups = provider.get_candidate_parent_groups()

        if group in parent_groups:
            parent_groups.remove((group.id, group.name))
    else:
        parent_groups = provider.get_groups()

    form.owner_id.choices = [(u.id, u.username + ' (' + u.fullname + ')')
                             for u in provider.get_people()]
    if request.authenticated_userid:
        form.owner_id.data = request.get_user.id
    else:
        form.owner_id.choices.insert(0, (-1, _(u'-- Select a username --')))

    form.parent_group_id.choices = [
        (group.id, group.name) for group in parent_groups]
    form.parent_group_id.choices.insert(0, (-1, _(u'-- None --')))
    form.group_type_id.choices = [
        (t.id, t.name) for t in provider.get_group_types()]
    form.group_type_id.choices.insert(0, (-1, _(u'-- Select a group type --')))
    form.certificate_id.choices = [
        (cert.id, cert.name) for cert in provider.get_certificates()]
    form.certificate_id.choices.insert(0, (-1, _(u'-- None --')))

    if request.method is not 'POST':
        form.license_id.choices.insert(0, (-1, _(u'-- None --')))

    return form


def get_email_recipient(group, user):
    """
    Provides email's recipient available for a given group.

    :param group: The group to look up
    :type group: fas.models.group.Group
    :param user: Authenticated user
    :type user: fas.models.people.People
    :return: Returns email(s) recipient
    :rtype: str or list
    """
    if group.mailing_list:
        log.debug(
            'Found mailing list address %s for group %s, set it up as recipient.'
            % (group.mailing_list, group.name))
        recipient = group.mailing_list
    else:
        if len(group.members) > 1:
            recipient = [
                u.person.email for u in group.members if
                u.person.email != user.email]
        else:
            recipient = group.owner.email

    return recipient
