# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Xavier Lamien.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from . import (
    Base,
    GroupStatus,
    MembershipStatus,
    MembershipRole
)

from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    UnicodeText,
    DateTime,
    Sequence,
    Boolean,
    ForeignKey,
    Index,
    func,
    UniqueConstraint,
    false)

from sqlalchemy.orm import (
    relation,
    relationship,
    backref
)

from fas.models import AccountPermissionType as perm

from babel.dates import format_date

import datetime
from fas.util import utc_iso_format


class GroupType(Base):
    __tablename__ = 'group_type'
    id = Column(Integer, unique=True, primary_key=True)
    name = Column(UnicodeText, unique=True, nullable=False)
    comment = Column(UnicodeText, nullable=True)

    groups = relation('Groups', order_by='Groups.name')

    __table_args__ = (
        Index('group_type_name_idx', name),
    )


class Groups(Base):
    __tablename__ = 'group'
    id = Column(
        Integer,
        Sequence('group_seq', start=20000),
        primary_key=True)
    name = Column(Unicode(40), unique=True, nullable=False)
    display_name = Column(UnicodeText, nullable=True)
    description = Column(UnicodeText, nullable=True)
    status = Column(Integer, default=GroupStatus.INACTIVE)
    avatar = Column(UnicodeText, nullable=True)
    web_link = Column(UnicodeText, nullable=True)
    mailing_list = Column(UnicodeText, nullable=True)
    mailing_list_url = Column(UnicodeText, nullable=True)
    irc_channel = Column(UnicodeText, nullable=True)
    irc_network = Column(UnicodeText, nullable=True)
    owner_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    group_type = Column(Integer, ForeignKey('group_type.id'), default=-1)
    parent_group_id = Column(Integer, ForeignKey('group.id'), default=-1)
    private = Column(Boolean, default=False)
    self_removal = Column(Boolean, default=True)
    need_approval = Column(Boolean, default=False)
    invite_only = Column(Boolean, default=False)
    join_msg = Column(UnicodeText, nullable=True)
    apply_rules = Column(UnicodeText, nullable=True)
    bound_to_github = Column(Boolean, default=False)
    license_sign_up = Column(
        Integer,
        ForeignKey('license_agreement.id'),
        default=-1
    )
    certificate = Column(Integer, ForeignKey('certificates.id'), default=-1)
    created = Column(
        DateTime, nullable=False,
        default=func.current_timestamp()
    )
    updated = Column(
        DateTime, nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    members = relationship(
        'GroupMembership',
        primaryjoin='and_(GroupMembership.group_id==Groups.id)',
        backref=backref('group', lazy='joined')
    )
    owner = relationship(
        'People',
        uselist=False
    )
    group_types = relation(
        'GroupType',
        uselist=False
    )
    parent_group = relation(
        'Groups',
        foreign_keys='Groups.id',
        primaryjoin='and_(Groups.id==Groups.parent_group_id)',
        uselist=False
    )
    license = relation(
        'LicenseAgreement',
        uselist=False
    )

    __table_args__ = (
        Index('group_name_idx', name),
    )

    def to_json(self, permissions):
        """ Return a JSON/dict representation of a Group object. """
        info = {}
        if permissions >= perm.CAN_READ_PUBLIC_INFO:
            info = {
                'name': self.name,
                'displayName': self.display_name,
                'picture': self.avatar,
                'url': self.web_link,
                'mailingList': self.mailing_list,
                'mailingListUrl': self.mailing_list_url,
                'ircChannel': self.irc_channel,
                'ircNetwork': self.irc_network,
                'owner': self.owner.username,
                'selfRemoval': self.self_removal,
                'needApproval': self.need_approval,
                'isInviteOnly': self.invite_only,
                'isPrivate': self.private,
                'status': self.status,
                'creationDate': utc_iso_format(self.created),
            }

        if self.group_types:
            info['groupType'] = self.group_types.name

        if self.parent_group:
            info['parentGroup'] = self.parent_group.name

        if permissions >= perm.CAN_READ_PEOPLE_FULL_INFO and self.members:
            info['members'] = []
            for member in self.members:
                info['members'].append(
                    {
                        'id': member.people_id,
                        'name': member.person.username,
                        'role': member.role,
                        'sponsor': member.sponsor,
                        'membershipStatus': member.status,
                        'status': member.person.status,
                        'ircnick': member.person.ircnick,
                        'joinedDate': utc_iso_format(member.approval_timestamp)
                    }
                )

        return info


class GroupMembership(Base):
    """ A mapping object to SQL GroupMembership table. """
    __tablename__ = 'group_membership'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('group.id'))
    role = Column(Integer, default=MembershipRole.USER)
    status = Column(Integer, default=MembershipStatus)
    comment = Column(UnicodeText, nullable=True)
    people_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    sponsor = Column(Integer, ForeignKey('people.id'), nullable=True)
    creation_timestamp = Column(DateTime, default=datetime.datetime.now)
    approval_timestamp = Column(DateTime, default=datetime.datetime.now)

    # role_level = relation(
    # 'RoleLevel',
    #     foreign_keys='RoleLevel.id',
    #     primaryjoin='and_(GroupMembership.role==RoleLevel.id)',
    #     uselist=False
    # )

    person = relationship(
        'People',
        foreign_keys='People.id',
        primaryjoin='and_(GroupMembership.people_id==People.id)',
        uselist=False
    )
    sponsors = relation(
        'People',
        foreign_keys='People.id',
        primaryjoin='and_(GroupMembership.sponsor==People.id)'
    )

    __table_args__ = (
        Index('people_roles_idx', role),
        UniqueConstraint('group_id', 'people_id'),
    )

    def get_status(self):
        """ Returns membership status of instantiated `People` """
        return MembershipStatus[self.status]

    def get_role(self, index=None):
        """ Returns membership role of instantiated `People` """
        if index is not None:
            return MembershipRole(index)

        return MembershipRole(self.role)

    def get_approval_date(self, request):
        """ Return approval date in human readable format. """
        date = self.approval_timestamp.date()

        return format_date(date, locale=request.locale_name)
