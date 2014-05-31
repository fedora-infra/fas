# -*- coding: utf-8 -*-

import pygeoip

from . import get_config


def get_record_from(ip):
    """ Get record from given IP. """
    gi = pygeoip.GeoIP(get_config('geoip.4.data.city'))

    return gi.record_by_addr(str(ip))