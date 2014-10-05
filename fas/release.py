# -*- coding: utf-8 -*-

from fas.utils import _

'''
Release informations about software
'''

__VERSION__ = '3.0.0'
__NAME__ = 'fas'
__DESC__ = 'The Fedora Account System'
__LONG_DESC__ = _(u'''
Manage contributors\' accounts and groups\'s involments
to the Fedora Project.
''')
__AUTHOR__ = 'Xavier Lamien'
__EMAIL__ = 'laxathom@fedoraproject.org'
__COPYRIGHT__ = _(u'© 2014')

__URL__ = 'https://github.com/fedora-infra/fas'
__DOWNLOAD_URL__ = 'https://github.com/fedora-infra/fas/releases'
__LICENSE__ = ''


def get_release_info(request):
    """ returns release information in dict() format."""
    return {
        'name': __NAME__,
        'version': __VERSION__,
        'description': __DESC__,
        'long_description': __LONG_DESC__,
        'authors': __AUTHOR__,
        'copyright': __COPYRIGHT__,
        'url': __URL__,
        'download_url': __DOWNLOAD_URL__,
        'license': __LICENSE__
        }
