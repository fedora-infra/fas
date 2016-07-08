# -*- coding: utf-8 -*-
#
# Copyright © 2012 Patrick Uiterwijk
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Patrick Uiterwijk <puiterwijk@fedoraproject.org>
#

import cherrypy
import time
from turbogears import config
import requests


def recursive_str(dct):
    """ This function makes sure that dct is json serializable. """
    if not hasattr(dct, '__iter__'):
            return str(dct)
    for key in dct:
        if isinstance(dct[key], dict):
            dct[key] = recursive_str(dct[key])
        elif isinstance(dct[key], list):
            dct[key] = map(recursive_str, dct[key])
        elif isinstance(dct[key], unicode):
            dct[key] = str(dct[key].encode('utf-8'))
        else:
            # If it's not a dict or list, just run an str() over it
            dct[key] = str(dct[key])
    return dct

def submit_to_spamcheck(action, data):
    """ This function submits to spamcheck. Caller is responsible for catching errors."""
    submit_data = recursive_str(data)
    submit_data['request_headers'] = cherrypy.request.headers
    return requests.post(config.get('antispam.api.url'),
        auth=(config.get('antispam.api.username'),
              config.get('antispam.api.password')),
        json={'action': action,
              'time': int(time.time()),
              'data': submit_data})
