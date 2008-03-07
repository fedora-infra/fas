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
    p.password = password
    p.comments = comments
    p.postal_address = postal_address
    p.telephone = telephone
    p.creation = creation
    p.internal_comments = internal_comments
    p.ircnick = ircnick
    p.status = 'active'
    try:
        session.flush()
    except IntegrityError, e:
        print "\tCould not create %s - %s" % (username, e)
        session.close()
        continue

    person_email = PersonEmails()
    try:
        person_email.email = email
    except AttributeError:
        print "\tCould not create email for %s (%s)" % (username, email)
        session.close()
        continue
    person_email.person = p
    person_email.description = 'Fedora Email'
    person_email.verified = True # The first email is verified for free, since this is where their password is sent.
    session.flush()
    
    
    email_purpose = EmailPurposes()
    email_purpose.person = p
    email_purpose.person_email = person_email
    email_purpose.purpose = 'primary'
    session.flush()

c.execute('select id, name, owner_id, group_type, needs_sponsor, user_can_remove, prerequisite_id, joinmsg from project_group order by id;')
bool_dict = {'f' : False, 't' : True}
print "Creating Groups..."
for group in c.fetchall():
    (id, name, owner_id, group_type, needs_sponsor, user_can_remove, prerequisite_id, joinmsg) = group
    print "%i - %s" % (id, name)
    try:
        group = Groups()
        group.id = id
        group.name = name
        group.display_name = name
        group.owner_id = owner_id
        group.group_type = group_type
        group.needs_sponsor = bool(bool_dict(needs_sponsor))
        group.user_can_remove = bool(bool_dict(user_can_remove))
        if prerequisite_id:
            prerequisite = Groups.by_id(prerequisite_id)
            group.prerequisite = prerequisite
        group.joinmsg = joinmsg
        # Log here
        session.flush()
    except TypeError:
        print "The group: '%s' could not be created." % groupname

c.execute('select person_id, project_group_id, role_type, role_domain, role_status, internal_comments, sponsor_id, creation, approval from role order by person_id;')
print "Creating Role Maps..."
for role in c.fetchall():
    (person_id, project_group_id, role_type, role_domain, role_status, internal_comments, sponsor_id, creation, approval) = role
    print "%s - %s" % (person_id, project_group_id)
    role = PersonRoles()
    role.role_status = role_status
    role.role_type = role_type
    role.member = People.by_id(person_id)
    role.group = Group.by_id(group_id)
    
