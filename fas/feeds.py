# -*- coding: utf-8 -*-
''' Provides feeds interface to FAS '''
#
# Copyright © 2008  Ricky Zhou
# Copyright © 2008 Red Hat, Inc.
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
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
#
import urllib
from xml.dom import minidom


class Koji:
    ''' Provide fas feeds for koji '''
    def __init__(self, user_name,
                url='http://publictest8/koji/recentbuilds?user='):
        build_feed = minidom.parse(urllib.urlopen(url + user_name))
        try:
            self.user_link = build_feed.getElementsByTagName(
                            'link')[0].childNodes[0].data
            self.builds = {}
            for build in build_feed.getElementsByTagName('item'):
                link = build.getElementsByTagName('link')[0].childNodes[0].data
                self.builds[link] = {}
                self.builds[link]['title'] = build.getElementsByTagName(
                                            'title')[0].childNodes[0].data
                self.builds[link]['pubDate'] = build.getElementsByTagName(
                                            'pubDate')[0].childNodes[0].data
        except IndexError:
            return
