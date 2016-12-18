# -*- coding: utf-8 -*-
#
# Copyright © 2014 - 2016 Xavier Lamien.
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
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

'''
Release information about software
'''

__VERSION__ = '3.0.1'
__NAME__ = 'fas'
__DESC__ = 'The Fedora Account System'
__LONG_DESC__ = u'''
The Fedora Account System is a community oriented accounts system which
aims to provide a self-driven and self-controled management to 
its registered users.
'''
__AUTHOR__ = 'Xavier Lamien'
__EMAIL__ = 'laxathom@fedoraproject.org'
__COPYRIGHT__ = u'© 2014 - 2016'

__URL__ = 'https://github.com/fedora-infra/fas'
__DOWNLOAD_URL__ = 'https://github.com/fedora-infra/fas/releases'
__LICENSE__ = 'GPLv2'


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
