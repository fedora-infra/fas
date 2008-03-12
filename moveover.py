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


db = pgdb.connect(dsn='localhost', user='fedora', password='test', database='fedorausers')

c = db.cursor()

c.execute('select id, name, owner_id, group_type, needs_sponsor, user_can_remove, prerequisite_id, joinmsg from project_group;')
bool_dict = {0 : False, 1 : True}
print "Creating Groups..."
admin = People.by_username('admin')
admin_id = admin.id
for group in c.fetchall():
    (id, name, owner_id, group_type, needs_sponsor, user_can_remove, prerequisite_id, joinmsg) = group
    print "%i - %s" % (id, name)
    try:
        group = Groups.by_id(id)
        if prerequisite_id:
            group.prerequisite = Groups.by_id(prerequisite_id)
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
        role = PersonRoles.query.filter_by(person_id=person_id, group_id=project_group_id)
        if role_status == 'declined':
            ''' No longer exists '''
            continue
        # Do we need to do weird stuff to convert from no time zone to time zone?
        role.creation = creation
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
