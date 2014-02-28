from . import Base

from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    UnicodeText,
    DateTime,
    Sequence,
    Boolean,
    Numeric,
    Enum,
    Index,
    ForeignKey
    )

import datetime


class People(Base):
    __tablename__ = 'people'
    id = Column(Integer, Sequence('people_seq', start='10000'), primary_key=True)
    username = Column(Unicode(255), unique=True, nullable=False)
    password = Column(UnicodeText(), nullable=False)
    fullname = Column(UnicodeText(), nullable=False)
    ircnick = Column(UnicodeText(), unique=True, nullable=True)
    avatar = Column(UnicodeText(), nullable=True)
    postal_address = Column(UnicodeText(), nullable=False)
    country_code = Column(Unicode(2), nullable=True)
    locale = Column(UnicodeText, default=u'C')
    telephone = Column(UnicodeText(), nullable=True)
    facsimile = Column(UnicodeText(), nullable=True)
    affiliation = Column(UnicodeText(), nullable=True)
    comment = Column(UnicodeText(), nullable=True)
    timezone = Column(UnicodeText(), default=u'UTC')
    gpg_id = Column(UnicodeText(), nullable=True)
    gpg_fingerprint = Column(UnicodeText(), nullable=True)
    ssh_key = Column(UnicodeText(), nullable=True)
    email = Column(UnicodeText(), unique=True, nullable=False)
    email_token = Column(UnicodeText(), unique=True, nullable=True)
    unverified_email = Column(UnicodeText(), nullable=True)
    security_question = Column(UnicodeText(), default=u'-')
    security_answer = Column(UnicodeText(), default=u'-')
    password_token = Column(UnicodeText(), nullable=True)
    old_password = Column(UnicodeText(), nullable=True)
    certificate_serial = Column(Integer, default=1)
    status = Column(Enum, default=1)
    status_change = Column(DateTime, default=datetime.datetime.utcnow)
    privacy = Column(Boolean, default=False)
    email_alias = Column(Boolean, default=True)
    blog_rss = Column(UnicodeText(), nullable=False)
    latitude = Column(Numeric, nullable=True)
    longitude = Column(Numeric, nullable=True)
    fas_token = Column(UnicodeText(), nullable=True)
    github_token = Column(UnicodeText(), nullable=True)
    twitter_token = Column(UnicodeText(), nullable=True)
    last_logged = Column(DateTime, default=datetime.datetime.utcnow)

Index('people_username_idx', People.username)


class PeopleAccountActivitiesLog(Base):
    __tablename__ = 'people_activity_log'
    id = Column(Integer, primary_key=True)
    people = Column(Integer, ForeignKey('people.id'), nullable=False)
    location = Column(Numeric, nullable=False)
    access_from = Column(UnicodeText(), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow())

Index('account_access_log_idx', PeopleAccountActivitiesLog.location)


class PeopleVirtualAccount(Base):
    __tablename__ = 'virtual_people'
    id = Column(Integer, unique=True, primary_key=True)
    username = Column(UnicodeText(), unique=True, nullable=False)
    parent = Column(Integer, ForeignKey('people.id'), nullable=False)
    type = Column(Integer, default=1)
    last_logged = Column(DateTime, default=datetime.datetime.utcnow)
