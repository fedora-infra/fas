# -*- coding: utf-8 -*-
#
# Copyright © 2014-2016 Xavier Lamien.
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
# __author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from enum import IntEnum
from pyramid.view import view_config
from fas.util import compute_list_pages_from, utc_iso_format

import datetime
import fas.release as fas_release

VERSION = '0.1'


class RequestStatus(IntEnum):
    SUCCESS = 0
    FAILED = 1


class BadRequest(Exception):
    pass


class NotFound(Exception):
    pass


class MetaData(object):

    def __init__(self, name=None):
        self.data = {}
        self.name = name

        self.datetime = datetime.datetime
        self.timestamp = utc_iso_format(self.datetime.utcnow())

        build = self.data['Build'] = {}
        build['name'] = u'FAS-%s' % fas_release.__VERSION__
        build['api_version'] = VERSION

    def set_name(self, name):
        """
        Set or update Metadata name.

        :param name: metadata name
        :type name: str
        """
        self.name = name

    def set_status(self, status):
        """
        Set status' request into metadata response.

        :param status: status code
        :type status: int
        """
        self.data['Status'] = status

    def set_error_msg(self, name='', text=''):
        """
        Set error message into metadata.

        :param name: Error name
        :param text: Error message
        """
        self.data['Error'] = {}
        self.data['Error']['name'] = name
        self.data['Error']['text'] = text

    def set_pages(self, items_nb, current=1, limit=0):
        """ Set page items into metadata's dictionary.

        :param items_nb: items number to build pages from.
        :type items_nb: int
        :param current: current page of items to display.
        :type current: int
        :param limit: number of items to display per page.
        :type limit: int
        """
        pages = compute_list_pages_from(items_nb, limit)

        self.data['Pages'] = {}
        self.data['Pages']['current'] = current
        self.data['Pages']['total'] = pages

    def set_data(self, data):
        """ Add data infos to metadata's dictionary.

        :param data: dictionary of requested infos.
        :type data: dict | list
        """
        self.data[self.name] = data

    def get_metadata(self):
        """ Get structured metadata.

        :returns: Dictionary of structured metadata from init object.
        :rtype: dict
        """
        self.data['StartTimeStamp'] = self.timestamp
        self.data['EndTimeStamp'] = utc_iso_format(self.datetime.utcnow())

        return self.data


@view_config(route_name='api', renderer='/api_home.xhtml')
def api_home(request):
    return {}

