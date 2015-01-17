# -*- coding: utf-8 -*-

from pyramid.view import view_config
from math import ceil

from fas.utils import compute_list_pages_from, fix_utc_iso_format

import datetime


class BadRequest(Exception):
    pass


class NotFound(Exception):
    pass


class MetaData():

    def __init__(self, name=None):
        self.data = {}
        # self.metadata[name + 'Result'] = {}
        self.name = name
        self.datetime = datetime.datetime
        self.timestamp = fix_utc_iso_format(self.datetime.utcnow())

    def set_error_msg(self, name='', text=''):
        """ Set error message into metadata's dict().

        :arg name: String, error name.
        :arg text: String, text that describe the error.
        """
        self.data['Error'] = {}
        self.data['Error']['Name'] = name
        self.data['Error']['Text'] = text

    def set_pages(self, obj, current=1, limit=0):
        """ Set page items into metadata's ditc().

        :arg current: int, current given page of request.
        :arg total: int, total page grom request based on item's limit.
        """
        pages = compute_list_pages_from(obj, limit)[0]
        # pages = ceil(float(count) / float(limit))

        self.data['Pages'] = {}
        self.data['Pages']['Current'] = current
        self.data['Pages']['Total'] = pages

    def set_data(self, data):
        """ Add data info to metadata dict.

        :arg data: dict or list of dict's object.
        """
        self.data[self.name] = data

    def get_metadata(self):
        """ get metadata from Request's object.

            :returns: Dict object of metadata from given parameters.
        """
        self.data['StartTimeStamp'] = self.timestamp
        self.data['EndTimeStamp'] = fix_utc_iso_format(self.datetime.utcnow())

        return self.data


@view_config(route_name='api_home', renderer='/api_home.xhtml')
def api_home(request):
    return {}
