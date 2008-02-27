#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright © 2007-2008  Red Hat, Inc. All rights reserved.
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
# Red Hat Author(s): Mike McGrath <mmcgrath@redhat.com>
#


from fedora.tg.client import BaseClient, AuthError, ServerError

import sys
import os
import logging

FAS_URL = 'http://localhost:8080/fas/json/'


class MakeShellAccounts(BaseClient):
    def group_list(self, search='*'):
        params = {'search' : search}
        data = self.send_request('group_list', auth=False, input=params)
        return data['group_list']
    
    def groups_text(self, groups=None, people=None):
        i = 0
        file = open('/tmp/group.txt', 'w')
        if not groups:
            groups = self.group_list()
        if not people:
            people = self.people_list()
        
        ''' First create all of our users/groups combo '''
        for person in people:
            uid = people[person]['id']
            username = people[person]['username']
            file.write("=%i %s:x:%i:\n" % (uid, username, uid))
            file.write( "0%i %s:x:%i:\n" % (i, username, uid))
            file.write( ".%s %s:x:%i:\n" % (username, username, uid))
            i = i + 1
        
        for group in groups:
            gid = groups[group]['id']
            name = groups[group]['name']
            file.write( "=%i %s:x:%i:\n" % (gid, name, gid))
            file.write("0%i %s:x:%i:\n" % (i, name, gid))
            file.write(".%s %s:x:%i:\n" % (name, name, gid))
            i = i + 1

        file.close()

        
    def people_list(self, search='*'):
        params = {'search' : search}
        data = self.send_request('people_list', auth=False, input=params)
        return data['people_list']

    def make_group_db(self):
        self.groups_text()
        os.system('makedb -o /tmp/group.db /tmp/group.txt')

if __name__ == '__main__':
    fas = MakeShellAccounts(FAS_URL, None, None, None)
    fas.make_group_db()
    
