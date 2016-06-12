# -*- coding: utf-8 -*-
#
# Copyright © 2014-2016 Xavier Lamien.
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
# __author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

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
    UniqueConstraint)
from sqlalchemy.orm import (
    relation,
    relationship,
    backref)
from . import Base
from enum import IntEnum
from fas.models.people import AccountPermissionType
from babel.dates import format_date
from fas.util import utc_iso_format
from fas import log
import datetime


class GroupStatus(IntEnum):
    INACTIVE = 0
    ACTIVE = 1
    PENDING = 3
    LOCKED = 5
    DISABLED = 8
    ARCHIVED = 10


class MembershipStatus(IntEnum):
    UNAPPROVED = 0
    APPROVED = 1
    PENDING = 2


class MembershipRole(IntEnum):
    UNKNOWN = 0
    USER = 1
    EDITOR = 2
    SPONSOR = 3
    ADMINISTRATOR = 4


class GroupType(Base):
    __tablename__ = 'group_type'
    id = Column(Integer, unique=True, primary_key=True)
    name = Column(UnicodeText, unique=True, nullable=False)
    comment = Column(UnicodeText, nullable=True)

    groups = relation('Groups', order_by='Groups.name')

    __table_args__ = (
        Index('group_type_name_idx', name),
    )

    def to_json(self):
        """
        Build a dict of GroupType model.

        :return: A dict format of registered `GroupType` models
        :rtype: dict
        """
        info = {
            'id': self.id,
            'name': self.name,
            'comment': self.comment
        }

        return info


class Groups(Base):
    __tablename__ = 'groups'
    id = Column(
        Integer,
        Sequence('groups_seq', start=20000),
        primary_key=True)
    name = Column(Unicode(40), unique=True, nullable=False)
    display_name = Column(UnicodeText, nullable=True)
    description = Column(UnicodeText, nullable=True)
    status = Column(Integer, default=GroupStatus.INACTIVE.value)
    avatar = Column(UnicodeText, nullable=True)
    web_link = Column(UnicodeText, nullable=True)
    mailing_list = Column(UnicodeText, nullable=True)
    mailing_list_url = Column(UnicodeText, nullable=True)
    irc_channel = Column(UnicodeText, nullable=True)
    irc_network = Column(UnicodeText, nullable=True)
    owner_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    group_type_id = Column(Integer, ForeignKey('group_type.id'), nullable=True)
    parent_group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    private = Column(Boolean, default=False)
    self_removal = Column(Boolean, default=True)
    need_approval = Column(Boolean, default=False)
    requires_sponsorship = Column(Boolean, default=False)
    requires_ssh = Column(Boolean, default=False)
    invite_only = Column(Boolean, default=False)
    join_msg = Column(UnicodeText, nullable=True)
    apply_rules = Column(UnicodeText, nullable=True)
    bound_to_github = Column(Boolean, default=False)
    license_id = Column(
        Integer,
        ForeignKey('license_agreement.id'),
        nullable=True
    )
    certificate_id = Column(Integer, ForeignKey('certificates.id'), nullable=True)
    creation_timestamp = Column(
        DateTime, nullable=False,
        default=func.current_timestamp()
    )
    update_timestamp = Column(
        DateTime, nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    members = relationship(
        'GroupMembership',
        primaryjoin='and_(GroupMembership.group_id==Groups.id)',
        backref=backref('group', lazy='joined',
                        single_parent=True,
                        cascade="save-update, delete, refresh-expire")
        # cascade_backrefs=True
    )
    owner = relationship(
        'People',
        primaryjoin='and_(People.id==Groups.owner_id)',
        uselist=False
    )
    group_type = relationship(
        'GroupType',
        primaryjoin='and_(GroupType.id==Groups.group_type_id)',
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
        foreign_keys='Groups.license_id',
        backref=backref('group', lazy='joined'),
        uselist=False
    )

    __table_args__ = (
        Index('groups_name_idx', name),
    )

    def get_status(self):
        """

        :return:
        :rtype:
        """
        return GroupStatus[self.status]

    def to_json(self, permissions, human_r=False):
        """ Return a JSON/dict representation of a Group object. """
        info = {}
        if permissions >= AccountPermissionType.CAN_READ_PUBLIC_INFO:
            info = {
                'id': self.id,
                'name': self.name,
                'display_name': self.display_name,
                'picture': self.avatar,
                'join_msg': self.join_msg,
                'url': self.web_link,
                'mailing_list': self.mailing_list,
                'mailing_list_url': self.mailing_list_url,
                'irc_channel': self.irc_channel,
                'irc_network': self.irc_network,
                'owner_id': self.owner.username if human_r else self.owner_id,
                'self_removal': self.self_removal,
                'need_approval': self.need_approval,
                'requires_sponsorship': self.requires_sponsorship,
                'invite_only': self.invite_only,
                'apply_rules': self.apply_rules,
                'private': self.private,
                'status': self.status,
                'creationDate': utc_iso_format(self.creation_timestamp),
            }

        if self.group_type:
            info['group_type'] = self.group_type.name if human_r else \
                self.group_type

        if self.parent_group:
            info['parent_group_id'] = self.parent_group.name if human_r else \
                self.parent_group.id

        if permissions >= AccountPermissionType.CAN_READ_PEOPLE_FULL_INFO and \
                self.members:
            info['members'] = []
            info['pending_requests'] = []
            for member in self.members:
                if member.person_id is None:
                    log.error('Got an empty People object from '
                              'group membership: %s.' % self.name)
                else:
                    person = {
                        'membership_id': member.id,
                        'person_id': member.person_id,
                        'person_name': member.person.username,
                        'role': MembershipRole(member.role).value,
                        'sponsor': member.sponsor_id,
                        'status': member.status,
                        'person_status': member.person.status,
                        'ircnick': member.person.ircnick,
                        'joined_datetime': utc_iso_format(
                            member.update_timestamp)
                    }
                    if member.status == MembershipStatus.APPROVED:
                        info['members'].append(person)
                    elif member.status == MembershipStatus.PENDING:
                        info['pending_requests'].append(person)

        return info


class GroupMembership(Base):
    """ A mapping object to SQL GroupMembership table. """
    __tablename__ = 'group_membership'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    role = Column(Integer, default=MembershipRole.USER.value)
    status = Column(Integer, default=MembershipStatus.UNAPPROVED.value)
    comment = Column(UnicodeText, nullable=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    sponsor_id = Column(Integer, ForeignKey('people.id'), nullable=True)
    creation_timestamp = Column(DateTime, default=datetime.datetime.now)
    update_timestamp = Column(DateTime, default=datetime.datetime.now)

    sponsors = relation(
        'People',
        foreign_keys='People.id',
        primaryjoin='and_(GroupMembership.sponsor_id==People.id)'
    )

    __table_args__ = (
        Index('people_roles_idx', role),
        UniqueConstraint('group_id', 'person_id'),
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
        date = self.update_timestamp.date()

        return format_date(date, locale=request.locale_name)
