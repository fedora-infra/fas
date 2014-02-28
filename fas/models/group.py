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
    Index
    )
import datetime

class GroupType(Base):
    __tablename__ = 'group_type'
    id = Column(Integer, unique=True, primary_key=True)
    name = Column(UnicodeText(), unique=True, nullable=False)
    comment = Column(UnicodeText(), nullable=True)

Index('group_type_name_idx', GroupType.name)

class Groups(Base):
    __tablename__ = 'group'
    id = Column(Integer, Sequence('group_seq', start=20000), primary_key=True)
    name = Column(Unicode(40), unique=True, nullable=False)
    display_name = Column(UnicodeText(), nullable=True)
    avatar = Column(UnicodeText(), nullable=True)
    web_link = Column(UnicodeText(), nullable=True)
    mailing_list = Column(UnicodeText(), nullable=True)
    mailing_list_url = Column(UnicodeText(), nullable=True)
    irc_channel = Column(UnicodeText(), nullable=True)
    irc_network = Column(UnicodeText(), nullable=True)
    owner = Column(Integer, ForeignKey('people.id'), nullable=False)
    group_type = Column(Integer, ForeignKey('group_type.id'), default=0)
    private = Column(Boolean, default=False)
    parent_group = Column(Integer, ForeignKey('group.id'), default=0)
    self_removal = Column(Boolean, default=True)
    need_approval = Column(Boolean, default=False)
    invite_only = Column(Boolean, default=False)
    join_msg = Column(UnicodeText(), nullable=True)
    apply_rules = Column(UnicodeText(), nullable=True)
    created = Column(DateTime, default=datetime.datetime.utcnow())

Index('group_name_idx', Groups.name)
