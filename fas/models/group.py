# -*- coding: utf-8 -*-

from . import Base

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
    )
from sqlalchemy.orm import relation
from fas.models import AccountPermissionType as perm

import datetime


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
    license_sign_up = Column(
        Integer,
        ForeignKey('license_agreement.id'),
        default=-1
    )
    created = Column(
        DateTime, nullable=False,
        default=func.current_timestamp()
    )
    updated = Column(
        DateTime, nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    members = relation(
        'GroupMembership',
        foreign_keys='GroupMembership.group_id',
        primaryjoin='and_(GroupMembership.group_id==Groups.id)',
        backref='group_membership'
    )
    owner = relation(
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

    __table_args__ = (
        Index('group_name_idx', name),
    )

    def to_json(self, permissions):
        """ Return a JSON/dict representation of a Group object. """
        info = {}
        if permissions >= perm.CAN_READ_PUBLIC_INFO:
            info = {
                'Name': self.name,
                'DisplayName': self.display_name,
                'Picture': self.avatar,
                'Url': self.web_link,
                'MailingList': self.mailing_list,
                'MailingListUrl': self.mailing_list_url,
                'IrcChannel': self.irc_channel,
                'IrcNetwork': self.irc_network,
                'Owner': self.owner.username,
                'SelfRemoval': self.self_removal,
                'NeedApproval': self.need_approval,
                'IsInviteOnly': self.invite_only,
                'IsPrivate': self.private,
                'CreationDate': self.created.strftime('%Y-%m-%d %H:%M'),
            }

        if self.group_types:
            info['GroupType'] = self.group_types.name

        if self.parent_group:
            info['ParentGroup'] = self.parent_group.name

        if permissions == perm.CAN_READ_PEOPLE_FULL_INFO:
            if self.members:
                info['Members'] = []
                for people in self.members:
                    # This is not optimum - send query on every loop
                    for user in people.people:
                        info['Members'].append(
                            {
                                'PeopleId': user.id,
                                'PeopleName': user.username,
                                'PeopleRole': people.role_level.role,
                                'GroupSponsor': people.sponsor
                            }
                        )

        return info


class GroupMembership(Base):
    __tablename__ = 'group_membership'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('group.id'))
    role = Column(Integer, ForeignKey('role_level.id'), default=1)
    status = Column(Integer, ForeignKey('account_status.id'), default=1)
    comment = Column(UnicodeText, nullable=True)
    people_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    sponsor = Column(Integer, ForeignKey('people.id'), nullable=False)
    creation_timestamp = Column(DateTime, default=datetime.datetime.now)
    approval_timestamp = Column(DateTime, default=datetime.datetime.now)

    role_level = relation(
        'RoleLevel',
        foreign_keys='RoleLevel.id',
        primaryjoin='and_(GroupMembership.role==RoleLevel.id)',
        uselist=False
    )

    account_status = relation(
        'AccountStatus',
        foreign_keys='AccountStatus.id',
        primaryjoin='and_(GroupMembership.status==AccountStatus.id)',
        uselist=False
    )

    group = relation(
        'Groups',
        foreign_keys='Groups.id',
        primaryjoin='and_(GroupMembership.group_id==Groups.id)',
        backref='group_membership',
        uselist=False
    )
    people = relation(
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
    )
