# -*- coding: utf-8 -*-

"""WebHelpers used in fas."""

from webhelpers import date, feedgenerator, html, number, misc, text

from fas.lib import release
from fas.lib.util import available_languages

from ipalib import api

#api.bootstrap(debug=False)
#api.finalize()
#api.Backend.xmlclient.connect()

def add_global_tmpl_vars():
    return dict(
            fas_version = release.VERSION,
            available_languages = available_languages(),
           )
