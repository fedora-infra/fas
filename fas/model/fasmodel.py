# -*- coding: utf-8 -*-
#
# Copyright © 2008  Red Hat, Inc. All rights reserved.
# Copyright © 2008  Ricky Zhou All rights reserved.
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
#            Ricky Zhou <ricky@fedoraproject.org>
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
from sqlalchemy import String, Integer, DateTime, Boolean
# A few sqlalchemy tricks:
# Allow viewing foreign key relations as a dictionary
from sqlalchemy.orm.collections import attribute_mapped_collection
# Allow us to reference the remote table of a many:many as a simple list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import and_, select

from sqlalchemy.exceptions import InvalidRequestError

from turbogears.database import session

from turbogears import identity, config

import turbogears

from fedora.tg.json import SABase
import fas
from fas import SHARE_CC_GROUP, SHARE_LOC_GROUP

# Bind us to the database defined in the config file.
get_engine()

#
# Tables Mapped from the DB
#

PeopleTable = Table('people', metadata, autoload=True)
PersonRolesTable = Table('person_roles', metadata, autoload=True)

ConfigsTable = Table('configs', metadata, autoload=True)
GroupsTable = Table('groups', metadata, autoload=True)
BugzillaQueueTable = Table('bugzilla_queue', metadata, autoload=True)
LogTable = Table('log', metadata, autoload=True)
RequestsTable = Table('requests', metadata, autoload=True)

SessionTable = Table('session', metadata, autoload=True)

#
# Selects for filtering roles
#
ApprovedRolesSelect = PersonRolesTable.select(and_(
    PeopleTable.c.id==PersonRolesTable.c.person_id,
    PersonRolesTable.c.role_status=='approved')).alias('approved')
UnApprovedRolesSelect = PersonRolesTable.select(and_(
    PeopleTable.c.id==PersonRolesTable.c.person_id,
    PersonRolesTable.c.role_status!='approved')).alias('unapproved')

#
# Selects for filtering people data
#
# The user can't see the *token fields or internal comments
PeopleSelfSelect = select((PeopleTable.c.id,
    PeopleTable.c.username,
    PeopleTable.c.human_name,
    PeopleTable.c.gpg_keyid,
    PeopleTable.c.ssh_key,
    PeopleTable.c.password,
    PeopleTable.c.password_changed,
    PeopleTable.c.email,
    PeopleTable.c.unverified_email,
    PeopleTable.c.comments,
    PeopleTable.c.postal_address,
    PeopleTable.c.country_code,
    PeopleTable.c.telephone,
    PeopleTable.c.facsimile,
    PeopleTable.c.affiliation,
    PeopleTable.c.certificate_serial,
    PeopleTable.c.creation,
    PeopleTable.c.ircnick,
    PeopleTable.c.last_seen,
    PeopleTable.c.status,
    PeopleTable.c.status_change,
    PeopleTable.c.locale,
    PeopleTable.c.timezone,
    PeopleTable.c.latitude,
    PeopleTable.c.longitude)).alias('people')

# Additionally remove telephone/facimile, postal_address, and password fields
PeopleOtherPublicSelect = select((PeopleTable.c.id,
    PeopleTable.c.username,
    PeopleTable.c.human_name,
    PeopleTable.c.gpg_keyid,
    PeopleTable.c.ssh_key,
    PeopleTable.c.email,
    PeopleTable.c.comments,
    PeopleTable.c.country_code,
    PeopleTable.c.affiliation,
    PeopleTable.c.certificate_serial,
    PeopleTable.c.creation,
    PeopleTable.c.ircnick,
    PeopleTable.c.last_seen,
    PeopleTable.c.status,
    PeopleTable.c.status_change,
    PeopleTable.c.locale,
    PeopleTable.c.timezone,
    PeopleTable.c.latitude,
    PeopleTable.c.longitude)).alias('people')
# If the user opts-out of the publicly available info, this all gets hidden
PeopleOtherPrivateSelect = select((PeopleTable.c.id,
    PeopleTable.c.username,
    PeopleTable.c.comments,
    PeopleTable.c.certificate_serial,
    PeopleTable.c.creation,
    PeopleTable.c.last_seen,
    PeopleTable.c.status,
    PeopleTable.c.status_change)).alias('people')
# If you're accessing this information anonymously, you get:
PeopleAnonSelect = select((PeopleTable.c.id,
    PeopleTable.c.username,
    PeopleTable.c.comments,
    PeopleTable.c.creation)).alias('people')

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
    Column('user_id', Integer, ForeignKey('people.id'), index=True),
    Column('ssl', Boolean)
)

#
# Mapped Classes
#

class People(SABase):
    '''Records for all the contributors to Fedora.'''

    admin_group = config.get('admingroup', 'accounts')
    system_group = config.get('systemgroup', 'fas-system')

    @classmethod
    def by_id(cls, id):
        '''
        A class method that can be used to search users
        based on their unique id
        '''
        return cls.query.filter_by(id=id).one()

    @classmethod
    def by_email_address(cls, email):
        '''
        A class method that can be used to search users
        based on their email addresses since it is unique.
        '''
        return cls.query.filter_by(email=email).one()

    @classmethod
    def by_username(cls, username):
        '''
        A class method that permits to search users
        based on their username attribute.
        '''
        return cls.query.filter_by(username=username).one()

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
        role.sponsor = requester
        role.approval = datetime.now(pytz.utc)
        cls._handle_auto_add(group, requester)

    def _handle_auto_add(cls, group, requester):
        """
        Handle automatic group approvals
        """
        auto_approve_groups = config.get('auto_approve_groups')
        associations = auto_approve_groups.split('|')
        approve_group_queue = []
        for association in associations:
            (groupname, approve_groups) = association.split(':', 1)
            if groupname == group.name:
                approve_group_queue.extend(approve_groups.split(','))
        for groupname in approve_group_queue:
            approve_group = Groups.by_name(groupname)
            cls._auto_add(approve_group, requester)

    def _auto_add(cls, group, requester):
        """
        Ensure that a person is approved in a group
        """
        try:
            role = PersonRoles.query.filter_by(member=cls, group=group).one()
            if role.role_status != 'approved':
                role.role_status = 'approved'
                role.sponsor = requester
                role.approval = datetime.now(pytz.utc)
        except InvalidRequestError:
            role = PersonRoles()
            role.member = cls
            role.group = group
            role.role_type = 'user'
            role.sponsor = requester
            role.role_status = 'approved'
            role.approval = datetime.now(pytz.utc)

    def remove(cls, group, requester):
        if not group in cls.memberships:
            raise fas.RemoveError, _('user is not a member')
        else:
            role = PersonRoles.query.filter_by(member=cls, group=group).one()
            session.delete(role)

    def set_share_cc(self, value):
        share_cc_group = Groups.by_name(SHARE_CC_GROUP)
        if value:
            try:
                self.apply(share_cc_group, self)
                self.sponsor(share_cc_group, self)
            except fas.ApplyError:
                pass
            except fas.SponsorError:
                pass
        else:
            try:
                self.remove(share_cc_group, self)
            except fas.SponsorError:
                pass

    def get_share_cc(self):
        return Groups.by_name(SHARE_CC_GROUP) in self.memberships

    def set_share_loc(self, value):
        share_loc_group = Groups.by_name(SHARE_LOC_GROUP)
        if value:
            try:
                self.apply(share_loc_group, self)
                self.sponsor(share_loc_group, self)
            except fas.ApplyError:
                pass
            except fas.SponsorError:
                pass
        else:
            try:
                self.remove(share_loc_group, self)
            except fas.SponsorError:
                pass

    def get_share_loc(self):
        return Groups.by_name(SHARE_LOC_GROUP) in self.memberships

    def filter_private(self):
        '''Filter out data marked private unless the user is authorized.

        Some data in this class can only be released if the user has not asked
        for it to be private.  Calling this method will filter the information
        out so it doesn't go anywhere.

        This method will return a data structure with the information allowed.
        If it's an admin, then the data structure will be self.  If it's
        anything else, parts of the information will be removed.  We do this by
        returning a mapped selectable that has less information in it.  Other
        than having less data, each of those objects should act the same way
        that this class does.

        Note that it is not foolproof.  For instance, a template could be
        written that traverses from people to groups to a different person
        and retrieves information from there.  However, this would not be a
        standard use of this method so we should know when we're doing
        non-standard things and filter the data there as well.
        '''
        # Full disclosure to admins
        if identity.current.in_group(admin_group) or \
                identity.current.in_group(system_group):
            return self

        # The user themselves gets everything except internal_comments
        if identity.current.user.username != self.username:
            return PeopleSelf.by_username(self.username)

        # Anonymous users get very little
        if identity.current.anonymous:
            return PeopleAnon.by_username(self.username)
        elif self.privacy:
            # Dealing with another user.  If the record they're viewing has
            # privact set, restrict what goes out more.
            return PeopleOtherPrivate.by_username(self.username)
        else:
            # All other people can get a moderate amount... but only if
            # privacy is not set.
            return PeopleOtherPublic.by_username(self.username)

    def __repr__(cls):
        return "User(%s,%s)" % (cls.username, cls.human_name)

    memberships = association_proxy('roles', 'group')
    approved_memberships = association_proxy('approved_roles', 'group')
    unapproved_memberships = association_proxy('unapproved_roles', 'group')

class PersonRoles(SABase):
    '''Record people that are members of groups.'''
    def __repr__(cls):
        return "PersonRole(%s,%s,%s,%s)" % (cls.member.username, cls.group.name, cls.role_type, cls.role_status)
    groupname = association_proxy('group', 'name')

class Configs(SABase):
    '''Configs for applications that a Fedora Contributor uses.'''
    pass

class Groups(SABase):
    '''Group that people can belong to.'''

    @classmethod
    def by_id(cls, group_id):
        '''
        A class method that can be used to search groups
        based on their unique id
        '''
        return cls.query.filter_by(id=group_id).one()

    @classmethod
    def by_email_address(cls, email):
        '''
        A class method that can be used to search groups
        based on their email addresses since it is unique.
        '''
        return cls.query.filter_by(email=email).one()


    @classmethod
    def by_name(cls, name):
        '''
        A class method that permits to search groups
        based on their name attribute.
        '''
        return cls.query.filter_by(name=name).one()

    def delete(cls):
        for role in cls.roles:
            session.delete(role)
        session.delete(cls)

    def __repr__(cls):
        return "Groups(%s,%s)" % (cls.name, cls.display_name)

    # People in the group
    people = association_proxy('roles', 'member')

    def __json__(self):
        '''We want to make sure we keep a tight reign on sensistive information.
        Thus we strip out certain information unless a user is an admin.

        Current access restrictions
        ===========================

        Anonymous users can see:
            :id: The id in the account system and on the shell servers
            :name: Username in FAS
            :display_name: Human name of the person
            :group_type: The type of group
            :needs_sponsor: Whether the group requirse a sponsor or not
            :user_can_remove: Whether users can remove themselves from the group
            :creation: Date this group was created
            :joinmsg: The join message for the group
            :prequisite_id: The prerequisite for the group
            :owner_id: The owner of the group

        Authenticated Users add:
            :email: The group email address

        Admins gets access to this final field as well:
            :unverified_email: An unverified email
            :email_token: The token for setting an email
        '''
        props = super(Groups, self).__json__()

        # These columns no longer exist, but here's an example of restricting info.
        #if identity.current.anonymous:
        #    # Anonymous users can't see any of these
        #    del props['email']

        #if not identity.in_group('fas-system'):
        #    if not identity.in_group('accounts'):
        #        # Only admins can see internal_comments
        #        del props['unverified_email']
        #        del props['emailtoken']

        return props

class BugzillaQueue(SABase):
    '''Queued up changes that need to be applied to bugzilla.'''
    def __repr__(cls):
        return "BugzillaQueue(%s,%s,%s,%s)" % (cls.person.username, cls.email, cls.group.name, cls.action)

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

# These classes are for mapping the People data with restrictions.  Since some
# of the information shouldn't be revealed, we map to selectables that only
# have the public data.
class PeopleSelf(People):
    pass

class PeopleAnon(People):
    pass

class PeopleOtherPrivate(People):
    pass

class PeopleOtherPublic(People):
    pass

#
# Classes for the SQLAlchemy Visit Manager
#

class Visit(SABase):
    '''Track how many people are visiting the website.

    It doesn't currently make sense for us to track this here so we clear this
    table of stale records every hour.
    '''
    @classmethod
    def lookup_visit(cls, visit_key):
        return cls.query.get(visit_key)

class VisitIdentity(SABase):
    '''Associate a user with a visit cookie.

    This allows users to log in to app.
    '''
    pass

class Session(SABase):
    '''Session'''
    pass

#
# set up mappers between tables and classes
#

mapper(Session, SessionTable)

#
# mappers for filtering roles
#
mapper(ApprovedRoles, ApprovedRolesSelect, properties = {
    'group': relation(Groups, backref='approved_roles', lazy = False)
    })
mapper(UnApprovedRoles, UnApprovedRolesSelect, properties = {
    'group': relation(Groups, backref='unapproved_roles', lazy = False)
    })


#
# Mappers for filtering People Information
#
mapper(PeopleSelf, PeopleSelfSelect, properties = {
    'group_roles': relation(PersonRoles,
        collection_class = attribute_mapped_collection('groupname'),
        primaryjoin = PeopleSelfSelect.c.id == PersonRolesTable.c.person_id),
    'approved_roles': relation(ApprovedRoles,
        primaryjoin = PeopleSelfSelect.c.id == ApprovedRoles.c.person_id),
    'unapproved_roles': relation(UnApprovedRoles,
        primaryjoin = PeopleSelfSelect.c.id == UnApprovedRoles.c.person_id)
    })

mapper(PeopleAnon, PeopleAnonSelect, properties = {
    'group_roles': relation(PersonRoles, viewonly=True,
        collection_class = attribute_mapped_collection('groupname'),
        primaryjoin = PeopleAnonSelect.c.id == PersonRolesTable.c.person_id),
    'approved_roles': relation(ApprovedRoles,
        primaryjoin = PeopleAnonSelect.c.id == ApprovedRoles.c.person_id),
    'unapproved_roles': relation(UnApprovedRoles,
        primaryjoin = PeopleAnonSelect.c.id == UnApprovedRoles.c.person_id)
    })

mapper(PeopleOtherPrivate, PeopleOtherPrivateSelect, properties = {
    'group_roles': relation(PersonRoles,
        collection_class = attribute_mapped_collection('groupname'),
        primaryjoin = PeopleOtherPrivateSelect.c.id \
                == PersonRolesTable.c.person_id),
    'approved_roles': relation(ApprovedRoles,
        primaryjoin = PeopleOtherPrivateSelect.c.id \
                == ApprovedRoles.c.person_id),
    'unapproved_roles': relation(UnApprovedRoles,
        primaryjoin = PeopleOtherPrivateSelect.c.id \
                == UnApprovedRoles.c.person_id)
    })

mapper(PeopleOtherPublic, PeopleOtherPublicSelect, properties = {
    'group_roles': relation(PersonRoles,
        collection_class = attribute_mapped_collection('groupname'),
        primaryjoin = PeopleOtherPublicSelect.c.id \
                == PersonRolesTable.c.person_id),
    'approved_roles': relation(ApprovedRoles,
        primaryjoin = PeopleOtherPublicSelect.c.id \
                == ApprovedRoles.c.person_id),
    'unapproved_roles': relation(UnApprovedRoles,
        primaryjoin = PeopleOtherPublicSelect.c.id \
                == UnApprovedRoles.c.person_id)
    })

#
# General Mappers
#

mapper(People, PeopleTable, properties = {
    # This name is kind of confusing.  It's to allow person.group_roles['groupname'] in order to make auth.py (hopefully) slightly faster.  
    'group_roles': relation(PersonRoles,
        collection_class = attribute_mapped_collection('groupname'),
        primaryjoin = PeopleTable.c.id==PersonRolesTable.c.person_id),
    'approved_roles': relation(ApprovedRoles, backref='member',
        primaryjoin = PeopleTable.c.id==ApprovedRoles.c.person_id),
    'unapproved_roles': relation(UnApprovedRoles, backref='member',
        primaryjoin = PeopleTable.c.id==UnApprovedRoles.c.person_id)
    })

mapper(PersonRoles, PersonRolesTable, properties = {
    'member': relation(People, backref = 'roles', lazy = False,
        primaryjoin=PersonRolesTable.c.person_id==PeopleTable.c.id),
    'group': relation(Groups, backref='roles', lazy = False,
        primaryjoin=PersonRolesTable.c.group_id==GroupsTable.c.id),
    'sponsor': relation(People, uselist=False,
        primaryjoin = PersonRolesTable.c.sponsor_id==PeopleTable.c.id)
    })
mapper(Configs, ConfigsTable, properties = {
    'person': relation(People, backref = 'configs')
    })
mapper(Groups, GroupsTable, properties = {
    'owner': relation(People, uselist=False,
        primaryjoin = GroupsTable.c.owner_id==PeopleTable.c.id),
    'prerequisite': relation(Groups, uselist=False,
        remote_side=[GroupsTable.c.id],
        primaryjoin = GroupsTable.c.prerequisite_id==GroupsTable.c.id)
    })
mapper(BugzillaQueue, BugzillaQueueTable, properties = {
    'group': relation(Groups, lazy = False, backref = 'pending'),
    'person': relation(People, lazy = False, backref = 'pending'),
    ### TODO: test to be sure SQLAlchemy only loads the backref on demand
    'author': relation(People, backref='changes')
    })
mapper(Requests, RequestsTable, properties = {
    'person': relation(People, backref='requests')
    })
mapper(Log, LogTable)

# TurboGears Identity
mapper(Visit, visits_table)
mapper(VisitIdentity, visit_identity_table,
        properties=dict(users=relation(People, backref='visit_identity')))
