# -*- coding: utf-8 -*-
#
# Copyright © 2008  Red Hat, Inc. All rights reserved.
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
# Author(s): Toshio Kuratomi <tkuratom@redhat.com>
#

'''
Model for the Fedora Account System
'''
from datetime import datetime
from turbogears.database import metadata, mapper, get_engine
# import some basic SQLAlchemy classes for declaring the data model
# (see http://www.sqlalchemy.org/docs/04/ormtutorial.html)
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import relation
# import some datatypes for table columns from SQLAlchemy
# (see http://www.sqlalchemy.org/docs/04/types.html for more)
from sqlalchemy import String, Unicode, Integer, DateTime
# A few sqlalchemy tricks:
# Allow viewing foreign key relations as a dictionary
from sqlalchemy.orm.collections import column_mapped_collection
# Allow us to reference the remote table of a many:many as a simple list
from sqlalchemy.ext.associationproxy import association_proxy

from turbogears import identity

from fas.json import SABase
# Soon we'll use this instead:
#from fedora.tg.json import SABase

# Bind us to the database defined in the config file.
get_engine()

#
# Tables Mapped from the DB
#

PeopleTable = Table('people', metadata, autoload=True)
PersonEmailsTable = Table('person_emails', metadata, autoload=True)
PersonRolesTable = Table('person_roles', metadata, autoload=True)
ConfigsTable = Table('configs', metadata, autoload=True)
GroupsTable = Table('groups', metadata, autoload=True)
GroupEmailsTable = Table('group_emails', metadata, autoload=True)
GroupRolesTable = Table('group_roles', metadata, autoload=True)
BugzillaQueueTable = Table('bugzilla_queue', metadata, autoload=True)

# The identity schema -- These must follow some conventions that TG
# understands and are shared with other Fedora services via the python-fedora
# module.

visits_table = Table('visit', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('created', DateTime, nullable=False, default=datetime.now),
    Column('expiry', DateTime)
)

visit_identity_table = Table('visit_identity', metadata,
    Column('visit_key', String(40), ForeignKey('visit.visit_key'),
        primary_key=True),
    Column('user_id', Integer, ForeignKey('people.id'), index=True)
)

#
# Mapped Classes
#

class People(SABase):
    '''Records for all the contributors to Fedora.'''
    pass
    memberships = association_proxy('roles', 'group')

# It's possible we want to merge this into the People class
'''
class User(object):
    """
    Reasonably basic User definition.
    Probably would want additional attributes.
    """
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms |= set(g.permissions)
        return perms
    permissions = property(permissions)

    def by_email_address(cls, email):
        """
        A class method that can be used to search users
        based on their email addresses since it is unique.
        """
        return cls.query.filter_by(email_address=email).first()

    by_email_address = classmethod(by_email_address)

    def by_user_name(cls, username):
        """
        A class method that permits to search users
        based on their user_name attribute.
        """
        return cls.query.filter_by(user_name=username).first()

    by_user_name = classmethod(by_user_name)

    def _set_password(self, password):
        """
        encrypts password on the fly using the encryption
        algo defined in the configuration
        """
        self._password = identity.encrypt_password(password)

    def _get_password(self):
        """
        returns password
        """
        return self._password

    password = property(_get_password, _set_password)
'''
class PersonEmails(SABase):
    '''Map a person to an email address.'''
    pass

class PersonRoles(SABase):
    '''Record people that are members of groups.'''
    pass

class Configs(SABase):
    '''Configs for applications that a Fedora Contributor uses.'''
    pass

class Groups(SABase):
    '''Group that people can belong to.'''
    pass
    # People in the group
    people = association_proxy('roles', 'member')
    # Groups in the group
    groups = association_proxy('group_members', 'member')
    # Groups that this group belongs to
    memberships = association_proxy('group_roles', 'group')

class GroupEmails(SABase):
    '''Map a group to an email address.'''
    pass

class GroupRoles(SABase):
    '''Record groups that are members of other groups.'''
    pass

class BugzillaQueue(SABase):
    '''Queued up changes that need to be applied to bugzilla.'''
    pass

class Visit(SABase):
    '''Track how many people are visiting the website.
    
    It doesn't currently make sense for us to track this here so we clear this
    table of stale records every hour.
    '''
    def lookup_visit(cls, visit_key):
        return cls.query.get(visit_key)
    lookup_visit = classmethod(lookup_visit)


class VisitIdentity(SABase):
    '''Associate a user with a visit cookie.
    
    This allows users to log in to app.
    '''
    pass

#
# set up mappers between tables and classes
#
mapper(People, PeopleTable)
mapper(PersonEmails, PersonEmailsTable, properties = {
    person: relation(People, backref = 'emails',
        collection_class = column_mapped_collection(
            PersonEmailsTable.c.purpose))
    })
mapper(PersonRoles, PersonRolesTable, properties = {
    member: relation(People, backref = 'roles'),
    group: relation(Groups, backref='roles')
    })
mapper(Configs, ConfigsTable, properties = {
    person: relation(People, backref = 'configs')
    })
mapper(Groups, GroupsTable)
mapper(GroupEmails, GroupEmailsTable, properties = {
    group: relation(Group, backref = 'emails',
        collection_class = column_mapped_collection(
            GroupEmailsTable.c.purpose))
    })
# GroupRoles are complex because the group is a member of a group and thus
# is referencing the same table.
mapper(GroupRoles, GroupRolesTable, properties = {
    member: relation(Groups, backref = 'group_roles',
        primaryjoin = GroupsTable.c.id==GroupRolesTable.c.member_id),
    group: relation(Groups, backref = 'group_members',
        primaryjoin = GroupsTable.c.id==GroupRolesTable.c.group_id)
    })
mapper(BugzillaQueue, BugzillaQueueTable, properties = {
    group: relation(Groups, backref = 'pending'),
    person: relation(People, backref = 'pending')
    })

# TurboGears Identity
mapper(Visit, visits_table)
mapper(VisitIdentity, visit_identity_table,
        properties=dict(users=relation(People, backref='visit_identity')))
