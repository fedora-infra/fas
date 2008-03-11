#!/usr/bin/python
import pgdb

from turbogears.view import engines
import turbogears.view
import turbogears.util as tg_util
from turbogears import view, database, errorhandling, config
from itertools import izip
from inspect import isclass
from turbogears import update_config, start_server
import cherrypy
cherrypy.lowercase_api = True
from os.path import *
import sys
import time
import crypt
import random

if len(sys.argv) > 1:
    update_config(configfile=sys.argv[1],
        modulename="fas.config")
elif exists(join(dirname(__file__), "setup.py")):
    update_config(configfile="dev.cfg",modulename="fas.config")
else:
    update_config(configfile="prod.cfg",modulename="fas.config")

from sqlalchemy import *
from sqlalchemy.exceptions import *
from fas.model import *


def generate_salt(length=8):
    chars = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    salt = ''
    for i in xrange(length):
        salt += random.choice(chars)
    return salt



db = pgdb.connect(dsn='localhost', user='fedora', password='test', database='fedorausers')

c = db.cursor()

c.execute('select id, username, email, human_name, gpg_keyid, ssh_key, password, comments, postal_address, telephone, affiliation, creation, approval_status, internal_comments, ircnick from person order by id;')

print "Converting People Table"
for person in c.fetchall():
    (id, username, email, human_name, gpg_keyid, ssh_key, password, comments, postal_address, telephone, affiliation, creation, approval_status, internal_comments, ircnick) = person
    print "\t%i - %s" % (id, username)
    p = People()
    p.id = id
    p.username = username
    p.human_name = human_name
    p.gpg_keyid = gpg_keyid
    p.ssh_key = ssh_key
    p.password = crypt.crypt(password, "$1$%s" % generate_salt(8))
    p.comments = comments
    p.postal_address = postal_address
    p.telephone = telephone
    p.creation = creation
    p.internal_comments = internal_comments
    p.ircnick = ircnick
    p.status = 'active'
    p.email = email
    try:
        session.flush()
    except IntegrityError, e:
        print "\tERROR - Could not create %s - %s" % (username, e)
        session.close()
        continue

c.execute('select id, name, owner_id, group_type, needs_sponsor, user_can_remove, prerequisite_id, joinmsg from project_group;')
bool_dict = {0 : False, 1 : True}
print "Creating Groups..."
admin = People.by_username('admin')
admin_id = admin.id
for group in c.fetchall():
    (id, name, owner_id, group_type, needs_sponsor, user_can_remove, prerequisite_id, joinmsg) = group
    print "%i - %s" % (id, name)
    try:
        group = Groups()
        group.id = id
        group.name = name
        group.display_name = name
        if owner_id == 100001:
            ''' Update to new admin id '''
            owner_id = admin_id
        group.owner_id = owner_id
        group.group_type = group_type
        group.needs_sponsor = bool(bool_dict[needs_sponsor])
        group.user_can_remove = bool(bool_dict[user_can_remove])
#        if prerequisite_id:
#            prerequisite = Groups.by_id(prerequisite_id)
#            group.prerequisite = prerequisite
        group.joinmsg = joinmsg
        # Log here
        session.flush()
    except IntegrityError, e:
        print "\tERROR - The group: '%s' (%i) could not be created - %s" % (name, id, e)
    except FlushError, e:
        print "\tERROR - The group: '%s' (%i) could not be created - %s" % (name, id, e)
    except InvalidRequestError, e:
        print "\tERROR - The group: '%s' (%i) could not be created - %s" % (name, id, e)

    session.close()

c.execute('select person_id, project_group_id, role_type, role_domain, role_status, internal_comments, sponsor_id, creation, approval from role order by person_id;')
print "Creating Role Maps..."
for role in c.fetchall():
    (person_id, project_group_id, role_type, role_domain, role_status, internal_comments, sponsor_id, creation, approval) = role
    print "%s - %s" % (person_id, project_group_id)
    try:
        role = PersonRoles()
        if len(role_status) > 10:
            role_status = 'approved'
        if role_status == 'declined':
            ''' No longer exists '''
            continue
        role.role_status = role_status
        role.role_type = role_type
        role.member = People.by_id(person_id)
        role.group = Groups.by_id(project_group_id)
        session.flush()
    except ProgrammingError, e:
        print "\tERROR - The role %s -> %s could not be created - %s" % (person_id, project_group_id, e)
        session.close()
    except IntegrityError, e:
        if e.message.find('dupilcate key'):
            print "\tERROR - The role %s -> %s already exists!  Skipping" % (person_id, project_group_id)
            session.close()
            continue
        print "\tERROR - The role %s -> %s could not be created - %s" % (person_id, project_group_id, e)
    session.close()
