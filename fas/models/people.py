from . import Base, AccountStatus

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
    ForeignKey,
    func,
    )
from sqlalchemy.orm import relation

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
    bugzilla_email = Column(UnicodeText(), unique=True, nullable=True)
    email_token = Column(UnicodeText(), unique=True, nullable=True)
    unverified_email = Column(UnicodeText(), nullable=True)
    security_question = Column(UnicodeText(), default=u'-')
    security_answer = Column(UnicodeText(), default=u'-')
    password_token = Column(UnicodeText(), nullable=True)
    old_password = Column(UnicodeText(), nullable=True)
    certificate_serial = Column(Integer, default=1)
    status_id = Column(Integer, ForeignKey('account_status.id'),
                       nullable=False, default=1)
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

    date_created = Column(DateTime, nullable=False,
                          default=func.current_timestamp())
    date_updated = Column(DateTime, nullable=False,
                          default=func.current_timestamp(),
                          onupdate=func.current_timestamp())

    status = relation("AccountStatus")

    __table_args__ = (
        Index('people_username_idx', username),
    )

    def to_json(self, filter_private=True):
        """ Return a json/dict representation of this user.

        Use the `filter_private` argument to retrieve all the information about
        the user or just the public information.
        By default only the public information are returned.
        """
        if filter_private:
            info = {
                'username': self.username,
                'fullname': self.fullname,
                'ircnick': self.ircnick,
                'avatar': self.avatar,
                'gpg_id': self.gpg_id,
                'email': self.email,
                'bugzilla_email': self.bugzilla_email or self.email,
                'blog_rss': self.blog_rss,
                'creation_date': self.date_created.strftime('%Y-%m-%d %H:%M'),
                'status': self.status.status
            }
        return info



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
    __table_args__ = (
        Index('people_access_log_idx', access_from),
    )

    id = Column(Integer, unique=True, primary_key=True)
    username = Column(UnicodeText(), unique=True, nullable=False)
    parent = Column(Integer, ForeignKey('people.id'), nullable=False)
    type = Column(Integer, default=1)
    last_logged = Column(DateTime, default=datetime.datetime.utcnow)
