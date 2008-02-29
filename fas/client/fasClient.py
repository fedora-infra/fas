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
# TODO: put tmp files in a 700 tmp dir

import sys
import os
import logging

from fedora.tg.client import BaseClient, AuthError, ServerError
from optparse import OptionParser
from shutil import move
from rhpl.translate import _

FAS_URL = 'http://localhost:8080/fas/'


parser = OptionParser()

parser.add_option('--nogroup',
                     dest = 'no_group',
                     default = False,
                     action = 'store_true',
                     help = _('Do not sync group information'))
parser.add_option('--nopasswd',
                     dest = 'no_passwd',
                     default = False,
                     action = 'store_true',
                     help = _('Do not sync passwd information'))
parser.add_option('--noshadow',
                     dest = 'no_shadow',
                     default = False,
                     action = 'store_true',
                     help = _('Do not sync shadow information'))
parser.add_option('-s', '--server',
                     dest = 'FAS_URL',
                     default = FAS_URL,
                     metavar = 'FAS_URL',
                     help = _('Specify URL of fas server (default "%default")'))


class MakeShellAccounts(BaseClient):
    def group_list(self, search='*'):
        params = {'search' : search}
        data = self.send_request('group/list', auth=True, input=params)
        return data

    def shadow_text(self, people=None):
        i = 0
        file = open('/tmp/shadow.txt', 'w')
        if not people:
            people = self.people_list()
        for person in people:
            uid = person['id']
            username = person['username']
            password = person['password']
            file.write("=%i %s:%s:99999:0:99999:7:::\n" % (uid, username, password))
            file.write("0%i %s:%s:99999:0:99999:7:::\n" % (i, username, password))
            file.write(".%s %s:%s:99999:0:99999:7:::\n" % (username, username, password))
            i = i + 1
        file.close()


    def passwd_text(self, people=None):
        i = 0
        file = open('/tmp/passwd.txt', 'w')
        if not people:
            people = self.people_list()
        for person in people:
            uid = person['id']
            username = person['username']
            human_name = person['human_name']
            home_dir = "/home/fedora/%s" % username
            shell = "/bin/bash"
            file.write("=%s %s:x:%i:%i:%s:%s:%s\n" % (uid, username, uid, uid, human_name, home_dir, shell))
            file.write("0%i %s:x:%i:%i:%s:%s:%s\n" % (i, username, uid, uid, human_name, home_dir, shell))
            file.write(".%s %s:x:%i:%i:%s:%s:%s\n" % (username, username, uid, uid, human_name, home_dir, shell))
            i = i + 1
        file.close()
    
    def groups_text(self, groups=None, people=None):
        i = 0
        file = open('/tmp/group.txt', 'w')
        if not groups:
            groups = self.group_list()
        if not people:
            people = self.people_list()
        
        ''' First create all of our users/groups combo '''
        usernames = {}
        for person in people:
            uid = person['id']
            username = person['username']
            usernames['%s' % uid] = username
            file.write("=%i %s:x:%i:\n" % (uid, username, uid))
            file.write( "0%i %s:x:%i:\n" % (i, username, uid))
            file.write( ".%s %s:x:%i:\n" % (username, username, uid))
            i = i + 1
        
        for group in groups['groups']:
            gid = group['id']
            name = group['name']
            memberships = ''
            try:
                ''' Shoot me now I know this isn't right '''
                members = []
                for member in  groups['memberships'][u'%s' % gid]:
                    members.append(usernames['%s' % member['person_id']])
                memberships = ','.join(members)
            except KeyError:
                ''' No users exist in the group '''
                pass
            file.write( "=%i %s:x:%i:%s\n" % (gid, name, gid, memberships))
            file.write("0%i %s:x:%i:%s\n" % (i, name, gid, memberships))
            file.write(".%s %s:x:%i:%s\n" % (name, name, gid, memberships))
            i = i + 1

        file.close()
        
    def people_list(self, search='*'):
        params = {'search' : search}
        data = self.send_request('user/list', auth=True, input=params)
        return data['people']

    def make_group_db(self):
        self.groups_text()
        os.system('makedb -o /tmp/group.db /tmp/group.txt')
    
    def make_passwd_db(self):
        self.passwd_text()
        os.system('makedb -o /tmp/passwd.db /tmp/passwd.txt')
    
    def make_shadow_db(self):
        self.shadow_text()
        os.system('makedb -o /tmp/shadow.db /tmp/shadow.txt')
    
    def install_passwd_db(self):
        try:
            move('/tmp/passwd.db', '/var/db/passwd.db')
        except IOError, e:
            print "ERROR: Could not write passwd db - %s" % e
    
    def install_shadow_db(self):
        try:
            move('/tmp/shadow.db', '/var/db/shadow.db')
        except IOError, e:
            print "ERROR: Could not write shadow db - %s" % e
    
    def install_group_db(self):
        try:
            move('/tmp/group.db', '/var/db/group.db')
        except IOError, e:
            print "ERROR: Could not write group db - %s" % e
        

if __name__ == '__main__':
    try:
        fas = MakeShellAccounts(FAS_URL, 'admin', 'admin', False)
    except AuthError, e:
        print e
        sys.exit(1)
    fas.make_group_db()
    fas.make_passwd_db()
    fas.make_shadow_db()
    fas.install_group_db()
    fas.install_passwd_db()
    fas.install_shadow_db()
    
