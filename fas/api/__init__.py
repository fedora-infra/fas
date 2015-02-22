# -*- coding: utf-8 -*-

from pyramid.view import view_config

from fas.utils import compute_list_pages_from, utc_iso_format

import datetime


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

    def set_error_msg(self, name='', text=''):
        """ Set error message into meta.

        :param name: Error name
        :param text: Error message
        """
        self.data['Error'] = {}
        self.data['Error']['Name'] = name
        self.data['Error']['Text'] = text

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
        self.data['Pages']['Current'] = current
        self.data['Pages']['Total'] = pages

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


@view_config(route_name='api_home', renderer='/api_home.xhtml')
def api_home(request):
    return {}

