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
import pytz
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
from sqlalchemy import select, and_

from turbogears.database import session

from turbogears import identity

import turbogears

from fedora.tg.json import SABase
import fas

# Bind us to the database defined in the config file.
get_engine()

#
# Tables Mapped from the DB
#

PeopleTable = Table('people', metadata, autoload=True)
# This is a view and therefore needs to have its key columns defined
PersonEmailsTable = Table('person_emailsv', metadata,
        Column('id', Integer, primary_key=True),
        Column('purpose', Unicode, primary_key=True),
        Column('person_id', Integer, ForeignKey('people.id')),
        autoload=True)
PersonRolesTable = Table('person_roles', metadata, autoload=True)
ConfigsTable = Table('configs', metadata, autoload=True)
GroupsTable = Table('groups', metadata, autoload=True)
# This is a view and therefore needs to have its key columns defined
GroupEmailsTable = Table('group_emailsv', metadata,
        Column('id', Integer, primary_key=True),
        Column('purpose', Unicode, primary_key=True),
        Column('person_id', Integer, ForeignKey('groups.id')),
        autoload=True)
GroupRolesTable = Table('group_roles', metadata, autoload=True)
BugzillaQueueTable = Table('bugzilla_queue', metadata, autoload=True)
LogTable = Table('log', metadata, autoload=True)
RequestsTable = Table('requests', metadata, autoload=True)

#
# Selects for filtering roles
#
ApprovedRolesSelect = PersonRolesTable.select(and_(
    PeopleTable.c.id==PersonRolesTable.c.person_id,
    PersonRolesTable.c.role_status=='approved')).alias('approved')
UnApprovedRolesSelect = PersonRolesTable.select(and_(
    PeopleTable.c.id==PersonRolesTable.c.person_id,
    PersonRolesTable.c.role_status!='approved')).alias('unapproved')

# The identity schema -- These must follow some conventions that TG
# understands and are shared with other Fedora services via the python-fedora
# module.

visits_table = Table('visit', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('created', DateTime, nullable=False, default=datetime.now(pytz.utc)),
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
    
    def by_email_address(cls, email):
        '''
        A class method that can be used to search users
        based on their email addresses since it is unique.
        '''
        return cls.query.join('emails').filter_by(email=email).first()

    by_email_address = classmethod(by_email_address)

    def by_username(cls, username):
        '''
        A class method that permits to search users
        based on their username attribute.
        '''
        return cls.query.filter_by(username=username).one()

    by_username = classmethod(by_username)

    # If we're going to do logging here, we'll have to pass the person that did the applying.
    def apply(cls, group, requester):
        '''
        Apply a person to a group
        '''
        if group in cls.memberships:
            raise fas.ApplyError, _('user is already in this group')
        else:
            role = PersonRoles()
            role.role_status = 'unapproved'
            role.role_type = 'user'
            role.member = cls
            role.group = group
        
    def approve(cls, group, requester):
        '''
        Approve a person in a group  - requester for logging purposes
        '''
        if group not in cls.unapproved_memberships:
            raise fas.ApproveError, _('user is not an unapproved member')
        else:
            role = PersonRoles.query.filter_by(member=cls, group=group).one()
            role.role_status = 'approved'
        
    def upgrade(cls, group, requester):
        '''
        Upgrade a user in a group - requester for logging purposes
        '''
        if not group in cls.memberships:
            raise fas.UpgradeError, _('user is not a member')
        else:
            role = PersonRoles.query.filter_by(member=cls, group=group).one()
            if role.role_type == 'administrator':
                raise fas.UpgradeError, _('administrators cannot be upgraded any further')
            elif role.role_type == 'sponsor':
                role.role_type = 'administrator'
            elif role.role_type == 'user':
                role.role_type = 'sponsor'
        
    def downgrade(cls, group, requester):
        '''
        Downgrade a user in a group - requester for logging purposes
        '''
        if not group in cls.memberships:
            raise fas.DowngradeError, _('user is not a member')
        else:
            role = PersonRoles.query.filter_by(member=cls, group=group).one()
            if role.role_type == 'user':
                raise fas.DowngradeError, _('users cannot be downgraded any further')
            elif role.role_type == 'sponsor':
                role.role_type = 'user'
            elif role.role_type == 'administrator':
                role.role_type = 'sponsor'
                
    def sponsor(cls, group, requester):
        # If we want to do logging, this might be the place.
        if not group in cls.unapproved_memberships:
            raise fas.SponsorError, _('user is not an unapproved member')
        role = PersonRoles.query.filter_by(member=cls, group=group).one()
        role.role_status = 'approved'
        role.sponsor_id = requester.id
        role.approval = datetime.now(pytz.utc)

    def remove(cls, group, requester):
        if not group in cls.memberships:
            raise fas.RemoveError, _('user is not a member')
        else:
            role = PersonRoles.query.filter_by(member=cls, group=group).one()
            session.delete(role)

    def __repr__(cls):
        return "User(%s,%s)" % (cls.username, cls.human_name)

    def __json__(self):
        '''We want to make sure we keep a tight reign on sensistive information.
        Thus we strip out certain information unless a user is an admin or the
        current user.

        Current access restrictions
        ===========================

        Anonymous users can see:
            :id: The id in the account system and on the shell servers
            :username: Username in FAS
            :human_name: Human name of the person
            :comments: Comments that the user leaves about themselves
            :creation: Date this account was created
            :ircnick: User's nickname on IRC
            :last_seen: timestamp the user last logged into anything tied to
                the account system 
            :status: Whether the user is active, inactive, on vacation, etc
            :status_change: timestamp that the status was last updated
            :locale: User's default locale for Fedora Services
            :timezone: User's timezone
            :latitude: Used for constructing maps of contributors
            :longitude: Used for contructing maps of contributors

        Authenticated Users add:
            :ssh_key: Public key for connecting to over ssh
            :gpg_keyid: gpg key of the user
            :affiliation: company or group the user wishes to identify with
            :certificate_serial: serial number of the user's Fedora SSL
                Certificate

        User Themselves add:
            :password: hashed password to identify the user
            :passwordtoken: used when the user needs to reset a password
            :postal_address: user's postal address
            :telephone: user's telephone number
            :facsimile: user's FAX number

        Admins gets access to this final field as well:
            :internal_comments: Comments an admin wants to write about a user

        Note: There are a few other resources that are not located directly in
        the People structure that you are likely to want to pass to consuming
        code like email address and groups.  Please see the documentation on
        SABase.__json__() to find out how to set jsonProps to handle those.
        '''
        props = super(People, self).__json__()
        if not identity.in_group('admin'):
            # Only admins can see internal_comments
            del props['internal_comments']
            if identity.current.anonymous:
                del props['ssh_key']
                del props['gpg_keyid']
                del props['affiliation']
                del props['certificate_serial']
                del props['password']
                del props['passwordtoken']
                del props['postal_address']
                del props['telephone']
                del props['facsimile']
                # Below should check for group accounts instead of a specific username
            elif not identity.current.user.username == self.username and not identity.current.user.username == 'admin':
                # Only an admin or the user themselves can see these fields
                del props['password']
                del props['passwordtoken']
                del props['postal_address']
                del props['telephone']
                del props['facsimile']

        return props

    memberships = association_proxy('roles', 'group')
    approved_memberships = association_proxy('approved_roles', 'group')
    unapproved_memberships = association_proxy('unapproved_roles', 'group')

# It's possible we want to merge this into the People class
'''
class User(object):
    """
    Reasonably basic User definition.
    Probably would want additional attributes.
    """
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
    def __repr__(cls):
        return "PersonRole(%s,%s,%s,%s)" % (cls.member.username, cls.group.name, cls.role_type, cls.role_status)

class Configs(SABase):
    '''Configs for applications that a Fedora Contributor uses.'''
    pass

class Groups(SABase):
    '''Group that people can belong to.'''
    def by_name(cls, name):
        '''
        A class method that permits to search groups
        based on their name attribute.
        '''
        return cls.query.filter_by(name=name).one()

    by_name = classmethod(by_name)


    def __repr__(cls):
        return "Groups(%s,%s)" % (cls.name, cls.display_name)

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

class Log(SABase):
    '''Write simple logs of changes to the database.'''
    pass

class Requests(SABase):
    '''
    Requests for certain resources may be restricted based on the user or host.
    '''
    pass

#
# Classes for mapping arbitrary selectables (This is similar to a view in
# python rather than in the db
#

class ApprovedRoles(PersonRoles):
    '''Only display roles that are approved.'''
    pass

class UnApprovedRoles(PersonRoles):
    '''Only show Roles that are not approved.'''
    pass

#
# Classes for the SQLAlchemy Visit Manager
#

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

#
# mappers for filtering roles
#
mapper(ApprovedRoles, ApprovedRolesSelect, properties = {
    'group': relation(Groups, backref='approved_roles')
    })
mapper(UnApprovedRoles, UnApprovedRolesSelect, properties = {
    'group': relation(Groups, backref='unapproved_roles')
    })

mapper(People, PeopleTable, properties = {
    'emails': relation(PersonEmails, backref = 'person',
        collection_class = column_mapped_collection(
            PersonEmailsTable.c.purpose)),
    'approved_roles': relation(ApprovedRoles, backref='member',
        primaryjoin = PeopleTable.c.id==ApprovedRoles.c.person_id),
    'unapproved_roles': relation(UnApprovedRoles, backref='member',
        primaryjoin = PeopleTable.c.id==UnApprovedRoles.c.person_id)
    })
mapper(PersonEmails, PersonEmailsTable)
mapper(PersonRoles, PersonRolesTable, properties = {
    'member': relation(People, backref = 'roles',
        primaryjoin=PersonRolesTable.c.person_id==PeopleTable.c.id),
    'group': relation(Groups, backref='roles'),
    'sponsor': relation(People, uselist=False,
        primaryjoin = PersonRolesTable.c.sponsor_id==PeopleTable.c.id)
    })
mapper(Configs, ConfigsTable, properties = {
    'person': relation(People, backref = 'configs')
    })
mapper(Groups, GroupsTable, properties = {
    'owner': relation(People, uselist=False,
        primaryjoin = GroupsTable.c.owner_id==PeopleTable.c.id),
    'emails': relation(GroupEmails, backref = 'group',
        collection_class = column_mapped_collection(
            GroupEmailsTable.c.purpose)),
    'prerequisite': relation(Groups, uselist=False,
        primaryjoin = GroupsTable.c.prerequisite_id==GroupsTable.c.id)
    })
mapper(GroupEmails, GroupEmailsTable)
# GroupRoles are complex because the group is a member of a group and thus
# is referencing the same table.
mapper(GroupRoles, GroupRolesTable, properties = {
    'member': relation(Groups, backref = 'group_roles',
        primaryjoin = GroupsTable.c.id==GroupRolesTable.c.member_id),
    'group': relation(Groups, backref = 'group_members',
        primaryjoin = GroupsTable.c.id==GroupRolesTable.c.group_id),
    'sponsor': relation(People, uselist=False,
        primaryjoin = GroupRolesTable.c.sponsor_id==PeopleTable.c.id)
    })
mapper(BugzillaQueue, BugzillaQueueTable, properties = {
    'group': relation(Groups, backref = 'pending'),
    'person': relation(People, backref = 'pending',
        primaryjoin=BugzillaQueueTable.c.person_id==PeopleTable.c.id)
    })
mapper(Log, LogTable, properties = {
    ### TODO: test to be sure SQLAlchemy only loads the backref on demand
    'author': relation(People, backref='changes')
    })
mapper(Requests, RequestsTable, properties = {
    'person': relation(People, backref='requests')
    })

# TurboGears Identity
mapper(Visit, visits_table)
mapper(VisitIdentity, visit_identity_table,
        properties=dict(users=relation(People, backref='visit_identity')))
