#!/usr/bin/python
import __main__
if not hasattr(__main__, '__requires__'):
    __main__.__requires__ = []
__main__.__requires__.append('SQLAlchemy >= 0.5, <= 0.6')

import sys
sys.stdout = sys.stderr

import pkg_resources
pkg_resources.require('SQLAlchemy')

import os
os.environ['PYTHON_EGG_CACHE'] = '/var/www/.python-eggs'

from pyramid.paster import get_app, setup_logging
ini_path = '~/.python/modwsgi/env/fas/production.ini'
setup_logging(ini_path)
application = get_app(ini_path, 'main')

