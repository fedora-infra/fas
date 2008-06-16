#!/usr/bin/python
# Note: this requires python-genshi 0.5 or higher to run (deps on NewTextTemplate)

import os
from fedora.accounts.fas2 import *
import ConfigParser
import optparse
import logging
from rhpl.translate import _
from genshi.template import NewTextTemplate
import md5
import tempfile
import codecs

import sys

from shutil import move, rmtree

log = logging.getLogger('fas')

parser = optparse.OptionParser()

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
parser.add_option('-s', '--server',
                  dest = 'FAS_URL',
                  default = None,
                  metavar = 'FAS_URL',
                  help = _('Specify URL of fas server.'))
parser.add_option('-d', '--display',
                  dest = 'display',
                  default = False,
                  action = 'store_true',
                  help = _('Print file to std out.'))
parser.add_option('-p', '--prefix',
                  dest = 'prefix',
                  default = None,
                  metavar = 'prefix',
                  help = _('Specify install prefix.  Useful for testing'))
parser.add_option('--debug',
                  dest = 'debug',
                  default = False,
                  action = 'store_true',
                  help = _('Enable debugging messages'))

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

FAS_URL = config.get('global', 'url').strip('"')
if opts.prefix:
    prefix = opts.prefix
else:
    prefix = config.get('global', 'prefix').strip('"')

def generateUsersConf(FAS_URL=FAS_URL):
    fas = AccountSystem(FAS_URL)
    
    fas.username = config.get('global', 'login').strip('"')
    fas.password = config.get('global', 'password').strip('"')
    if not fas.authenticate(fas.username, fas.password):
        print "Could not authenticate"
        sys.exit(-1)
    
    people = fas.people_by_id()
    
    asterisk_group = fas.group_by_name('cla_done')
    asterisk_attrs = fas.send_request('asterisk/dump')['asterisk_attrs']
    
    
    #for k, v in  asterisk_group.items():
    #    print k
    
    userids = [user[u'person_id'] for user in asterisk_group[u'approved_roles']]
    userids.sort()
    
    template = NewTextTemplate(""";
    [general]
    callwaiting = yes
    threewaycalling = yes
    callwaitingcallerid = yes
    transfer = yes
    canpark = yes
    cancallforward = yes
    callreturn = yes
    callgroup = 1
    pickupgroup = 1
    hassip = yes
    host = dynamic
    hasiax = no
    hash323 = no
    hasmanager = no
    hasvoicemail = yes
    realm = fedoraproject.org
    {% for userid, username, human_name, md5secret in users %}\
    
    [${username}]
    fullname = ${human_name}
    email = ${username}@fedoraproject.org
    secret = ${username}
    md5secret = ${md5secret}
    hasvoicemail = yes
    context = from-contributor
    alternateexts = ${userid}
    {% end %}\
    """)
    
    users = []
    for userid in userids:
        try:
            if asterisk_attrs[u'%s' % userid]['enabled'] == u'1':
                person = people[userid]
                users.append(('5%06d' % userid,
                        person[u'username'],
                        person[u'human_name'],
                        md5.new('%s:fedoraproject.org:%s' % (person[u'username'],
                                                            asterisk_attrs[u'%s' % userid]['pass'])).hexdigest()))
        except KeyError:
            pass
    
    return template.generate(users=users).render()

def mk_tempdir():
    temp = tempfile.mkdtemp('-tmp', 'fas-', os.path.join(prefix + config.get('global', 'temp').strip('"')))
    return temp

def rm_tempdir(temp):
    rmtree(temp)

def write_users_conf(contents, temp):
    users_conf_file = codecs.open(temp + '/users.conf', mode='w', encoding='utf-8')
    users_conf_file.write(contents)

def install_users_conf(temp):
    try:
        move(temp + '/users.conf', os.path.join(prefix + '/etc/asterisk/users.conf'))
    except IOError, e:
        print "ERROR: Could not write users.conf - %s" % e


if __name__ == '__main__':
    if opts.install:
        conf = generateUsersConf()
        temp = mk_tempdir()
        write_users_conf(conf, temp)
        install_users_conf(temp)
        rm_tempdir(temp)
    else:
        parser.print_help()