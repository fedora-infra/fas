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
import logging
import syslog
import os
import tempfile

from fedora.tg.client import BaseClient, AuthError, ServerError
from optparse import OptionParser
from shutil import move, rmtree, copytree
from rhpl.translate import _

import ConfigParser

parser = OptionParser()

parser.add_option('-i', '--install',
                     dest = 'install',
                     default = False,
                     action = 'store_true',
                     help = _('Download and sync most recent content'))
parser.add_option('-c', '--config',
                     dest = 'CONFIG_FILE',
                     default = '/etc/fas.conf',
                     metavar = 'CONFIG_FILE',
                     help = _('Specify config file (default "%default")'))
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
parser.add_option('--nohome',
                     dest = 'no_home_dirs',
                     default = False,
                     action = 'store_true',
                     help = _('Do not create home dirs'))
parser.add_option('--nossh',
                     dest = 'no_ssh_keys',
                     default = False,
                     action = 'store_true',
                     help = _('Do not create ssh keys'))

parser.add_option('-s', '--server',
                     dest = 'FAS_URL',
                     default = None,
                     metavar = 'FAS_URL',
                     help = _('Specify URL of fas server.'))
parser.add_option('-e', '--enable',
                     dest = 'enable',
                     default = False,
                     action = 'store_true',
                     help = _('Enable FAS synced shell accounts'))
parser.add_option('-d', '--disable',
                     dest = 'disable',
                     default = False,
                     action = 'store_true',
                     help = _('Disable FAS synced shell accounts'))

(opts, args) = parser.parse_args()

log = logging.getLogger('fas')

try:
    config = ConfigParser.ConfigParser()
    if os.path.exists(opts.CONFIG_FILE):
        config.read(opts.CONFIG_FILE)
    elif os.path.exists('fas.conf'):
        config.read('fas.conf')
        print >> sys.stderr, "Could not open %s, defaulting to ./fas.conf" % opts.CONFIG_FILE
    else:
        print >> sys.stderr, "Could not open %s." % opts.CONFIG_FILE
        sys.exit(5)
except ConfigParser.MissingSectionHeaderError, e:
        print >> sys.stderr, "Config file does not have proper formatting - %s" % e
        sys.exit(6)

FAS_URL = config.get('global', 'url')

def _chown(arg, dir_name, files):
    os.chown(dir_name, arg[0], arg[1])
    for file in files:
        os.chown(os.path.join(dir_name, file), arg[0], arg[1])

class MakeShellAccounts(BaseClient):
    temp = None
    groups = None
    people = None
    memberships = None
    group_mapping = {}
    
    def mk_tempdir(self):
        self.temp = tempfile.mkdtemp('-tmp', 'fas-', config.get('global', 'temp'))

    def rm_tempdir(self):
        rmtree(self.temp)
    
    def valid_user(self, username):
        valid_groups = config.get('host', 'groups').split(',') + \
            config.get('host', 'restricted_groups').split(',') + \
            config.get('host', 'ssh_restricted_groups').split(',')
        try:
            for group in valid_groups:
                if username in self.group_mapping[group]:
                    return True
        except KeyError:
            return False
        return False
    
    def ssh_key(self, person):
        ''' determine what ssh key a user should have '''
        for group in config.get('host', 'groups').split(','):
            try:
                if person['username'] in self.group_mapping[group]:
                    return person['ssh_key']
            except KeyError:
                print >> sys.stderr, '%s is could not be found in fas but was in your config under "groups"!' % group
                continue
        for group in config.get('host', 'restricted_groups').split(','):
            try:
                if person['username'] in self.group_mapping[group]:
                    return person['ssh_key']
            except KeyError:
                print >> sys.stderr, '%s is could not be found in fas but was in your config under "restricted_groups"!' % group
                continue
        for group in config.get('host', 'ssh_restricted_groups').split(','):
            try:
                if person['username'] in self.group_mapping[group]:
                    command = config.get('users', 'ssh_restricted_app')
                    options = config.get('users', 'ssh_key_options')
                    key = 'command="%s",%s %s' % (command, options, person['ssh_key'])
                    return key
            except KeyError:
                print >> sys.stderr, '%s is could not be found in fas but was in your config under "ssh_restricted_groups"!' % group
                continue
        return 'INVALID\n'
    def shell(self, username):
        ''' Determine what shell username should have '''
        for group in config.get('host', 'groups').split(','):
            try:
                if username in self.group_mapping[group]:
                    return config.get('users', 'shell')
            except KeyError:
                print >> sys.stderr, '%s is could not be found in fas but was in your config under "groups"!' % group
                continue
        for group in config.get('host', 'restricted_groups').split(','):
            try:
                if username in self.group_mapping[group]:
                    return config.get('users', 'restricted_shell')
            except KeyError:
                print >> sys.stderr, '%s is could not be found in fas but was in your config under "restricted_groups"!' % group
                continue
        for group in config.get('host', 'ssh_restricted_groups').split(','):
            try:
                if username in self.group_mapping[group]:
                    return config.get('users', 'ssh_restricted_shell')
            except KeyError:
                print >> sys.stderr, '%s is could not be found in fas but was in your config under "restricted_groups"!' % group
                continue

        print >> sys.stderr, 'Could not determine shell for %s.  Defaulting to /sbin/nologin' % username
        return '/sbin/nologin'

    def passwd_text(self, people=None):
        i = 0
        passwd_file = open(self.temp + '/passwd.txt', 'w')
        shadow_file = open(self.temp + '/shadow.txt', 'w')
        os.chmod(self.temp + '/shadow.txt', 00400)
        if not self.people:
            self.people = self.people_list()
        for person in self.people:
            username = person['username']
            if self.valid_user(username):
                uid = person['id']
                human_name = person['human_name']
                password = person['password']
                home_dir = "%s/%s" % (config.get('users', 'home'), username)
                shell = self.shell(username)
                passwd_file.write("=%s %s:x:%i:%i:%s:%s:%s\n" % (uid, username, uid, uid, human_name, home_dir, shell))
                passwd_file.write("0%i %s:x:%i:%i:%s:%s:%s\n" % (i, username, uid, uid, human_name, home_dir, shell))
                passwd_file.write(".%s %s:x:%i:%i:%s:%s:%s\n" % (username, username, uid, uid, human_name, home_dir, shell))
                shadow_file.write("=%i %s:%s:99999:0:99999:7:::\n" % (uid, username, password))
                shadow_file.write("0%i %s:%s:99999:0:99999:7:::\n" % (i, username, password))
                shadow_file.write(".%s %s:%s:99999:0:99999:7:::\n" % (username, username, password))
                i = i + 1
        passwd_file.close()
        shadow_file.close()
                
    def valid_user_group(self, person_id):
        ''' Determine if person is valid on this machine as defined in the
        config file.  I worry that this is going to be horribly inefficient
        with large numbers of users and groups.'''
        for member in self.memberships:
            for group in self.memberships[member]:
                if group['person_id'] == person_id:
                    return True
        return False


    def groups_text(self, groups=None, people=None):
        i = 0
        file = open(self.temp + '/group.txt', 'w')
        if not groups:
            groups = self.group_list()
        if not people:
            people = self.people_list()
        
        ''' First create all of our users/groups combo '''
        usernames = {}
        for person in people:
            uid = person['id']
            if self.valid_user_group(uid):
                username = person['username']
                usernames[uid] = username
                file.write("=%i %s:x:%i:\n" % (uid, username, uid))
                file.write("0%i %s:x:%i:\n" % (i, username, uid))
                file.write(".%s %s:x:%i:\n" % (username, username, uid))
                i = i + 1
        
        for group in groups:
            gid = group['id']
            name = group['name']
            try:
                ''' Shoot me now I know this isn't right '''
                members = []
                for member in self.memberships[name]:
                    members.append(usernames[member['person_id']])
                memberships = ','.join(members)
                self.group_mapping[name] = members
            except KeyError:
                ''' No users exist in the group '''
                pass
            file.write("=%i %s:x:%i:%s\n" % (gid, name, gid, memberships))
            file.write("0%i %s:x:%i:%s\n" % (i, name, gid, memberships))
            file.write(".%s %s:x:%i:%s\n" % (name, name, gid, memberships))
            i = i + 1

        file.close()

    def group_list(self, search='*'):
        params = {'search' : search}
        request = self.send_request('group/list', auth=True, input=params)
        self.groups = request['groups']
        self.memberships = request['memberships']
        return self.groups

    def people_list(self, search='*'):
        params = {'search' : search}
        self.people = self.send_request('user/list', auth=True, input=params)['people']
        return self.people

    def make_group_db(self):
        self.groups_text()
        os.system('makedb -o %s/group.db %s/group.txt' % (self.temp, self.temp))

    def make_passwd_db(self):
        self.passwd_text()
        os.system('makedb -o %s/passwd.db %s/passwd.txt' % (self.temp, self.temp))
        os.system('makedb -o %s/shadow.db %s/shadow.txt' % (self.temp, self.temp))
        os.chmod(self.temp + '/shadow.db', 00400)

    def install_passwd_db(self):
        try:
            move(self.temp + '/passwd.db', '/var/db/passwd.db')
        except IOError, e:
            print "ERROR: Could not write passwd db - %s" % e
    
    def install_shadow_db(self):
        try:
            move(self.temp + '/shadow.db', '/var/db/shadow.db')
        except IOError, e:
            print "ERROR: Could not write shadow db - %s" % e
    
    def install_group_db(self):
        try:
            move(self.temp + '/group.db', '/var/db/group.db')
        except IOError, e:
            print "ERROR: Could not write group db - %s" % e
    
    def create_homedirs(self):
        ''' Create homedirs and home base dir if they do not exist '''
        home_base = config.get('users', 'home')
        if not os.path.exists(home_base):
            os.makedirs(home_base, mode=0755)
        for person in self.people:
            home_dir = os.path.join(home_base, person['username'])
            if not os.path.exists(home_dir) and self.valid_user(person['username']):
                syslog.syslog('Creating homedir for %s' % person['username'])
                copytree('/etc/skel/', home_dir)
                os.path.walk(home_dir, _chown, [person['id'], person['id']])

    def remove_stale_homedirs(self):
        ''' Remove homedirs of users that no longer have access '''
        home_base = config.get('users', 'home')
        try:
            home_backup_dir = config.get('users', 'home_backup_dir')
        except ConfigParser.NoOptionError:
            home_backup_dir = '/var/tmp/'
        users = os.listdir(home_base)
        for user in users:
            if not self.valid_user(user):
                if not os.path.exists(home_backup_dir):
                    os.makedirs(home_backup_dir)
                syslog.syslog('Backed up %s to %s' % (user, home_backup_dir))
                move(os.path.join(home_base, user), os.path.join(home_backup_dir, user))

    def create_ssh_keys(self):
        ''' Create ssh keys '''
        home_base = config.get('users', 'home')
        for person in self.people:
            username = person['username']
            if self.valid_user(username):
                ssh_dir = os.path.join(home_base, username, '.ssh')
                if person['ssh_key']:
                    key = self.ssh_key(person)
                    if not os.path.exists(ssh_dir):
                        os.makedirs(ssh_dir, mode=0700)
                    f = open(os.path.join(ssh_dir, 'authorized_keys'), 'w')
                    f.write(key)
                    f.close()
                    os.chmod(os.path.join(ssh_dir, 'authorized_keys'), 0600)
                    os.path.walk(ssh_dir, _chown, [person['id'], person['id']])
                    
def enable():
    temp = tempfile.mkdtemp('-tmp', 'fas-', config.get('global', 'temp'))

    old = open('/etc/sysconfig/authconfig', 'r')
    new = open(temp + '/authconfig', 'w')
    for line in old:
        if line.startswith("USEDB"):
            new.write("USEDB=yes\n")
        else:
            new.write(line)
    new.close()
    old.close()
    try:
        move(temp + '/authconfig', '/etc/sysconfig/authconfig')
    except IOError, e:
        print "ERROR: Could not write /etc/sysconfig/authconfig - %s" % e
        sys.exit(5)
    os.system('/usr/sbin/authconfig --updateall')
    rmtree(temp)

def disable():
    temp = tempfile.mkdtemp('-tmp', 'fas-', config.get('global', 'temp'))
    old = open('/etc/sysconfig/authconfig', 'r')
    new = open(temp + '/authconfig', 'w')
    for line in old:
        if line.startswith("USEDB"):
            new.write("USEDB=no\n")
        else:
            new.write(line)
    old.close()
    new.close()
    try:
        move(temp + '/authconfig', '/etc/sysconfig/authconfig')
    except IOError, e:
        print "ERROR: Could not write /etc/sysconfig/authconfig - %s" % e
        sys.exit(5)
    os.system('/usr/sbin/authconfig --updateall')
    rmtree(temp)


if __name__ == '__main__':
    if opts.enable:
        enable()
    if opts.disable:
        disable()

    if opts.install:
        try:
            fas = MakeShellAccounts(FAS_URL, config.get('global', 'login'), config.get('global', 'password'), False)
        except AuthError, e:
            print >> sys.stderr, e
            sys.exit(1)
        fas.mk_tempdir()
        fas.make_group_db()
        fas.make_passwd_db()
        if not opts.no_group:
            fas.install_group_db()
        if not opts.no_passwd:
            fas.install_passwd_db()
        if not opts.no_shadow:
            fas.install_shadow_db()
        if not opts.no_home_dirs:
            fas.create_homedirs()
            fas.remove_stale_homedirs()
        if not opts.no_ssh_keys:
            fas.create_ssh_keys()
        fas.rm_tempdir()
    if not (opts.install or opts.enable or opts.disable):
        parser.print_help()
