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
import pytz
from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    UnicodeText,
    DateTime,
    Sequence,
    Boolean,
    Numeric,
    Index,
    ForeignKey,
    func
)
from sqlalchemy.orm import (
    relation,
    relationship,
    backref
)
from . import Base
from collections import OrderedDict
from fas.util import format_datetime, utc_iso_format
from enum import IntEnum

from sqlalchemy import types
from dateutil.tz import tzutc
from datetime import datetime


class UTCDateTime(types.TypeDecorator):
    impl = types.DateTime

    def process_bind_param(self, value, engine):
        if value is not None:
            return value.astimezone(tzutc())

    def process_result_value(self, value, engine):
        if value is not None:
            return datetime(value.year, value.month, value.day,
                            value.hour, value.minute, value.second,
                            tzinfo=tzutc())


class AccountStatus(IntEnum):
    """
    Describes the status of a registered person.
    """
    INACTIVE = 0
    ACTIVE = 1
    BOT = 2
    PENDING = 3
    ON_VACATION = 4
    LOCKED = 5
    LOCKED_BY_ADMIN = 6
    DISABLED = 8
    SPAMCHECK_AWAITING = 9
    SPAMCHECK_DENIED = 10
    SPAMCHECK_MANUAL = 11


class AccountPermissionType(IntEnum):
    """
    Describes the type of permissions a person can request
    or have over its account.
    """
    UNDEFINED = 0
    CAN_READ_PUBLIC_INFO = 1
    CAN_READ_PEOPLE_PUBLIC_INFO = 2
    CAN_READ_PEOPLE_FULL_INFO = 3
    CAN_READ_AND_EDIT_PEOPLE_INFO = 5
    CAN_EDIT_GROUP_INFO = 7
    CAN_EDIT_GROUP_MEMBERSHIP = 8
    CAN_READ_SETTINGS = 10
    CAN_READ_AND_EDIT_SETTINGS = 11


class AccountLogType(IntEnum):
    LOGGED_IN = 1
    ACCOUNT_UPDATE = 3
    REQUESTED_API_KEY = 4
    UPDATE_PASSWORD = 5
    ASKED_RESET_PASSWORD = 6
    RESET_PASSWORD = 7
    SIGNED_LICENSE = 10
    REVOKED_GROUP_MEMBERSHIP = 11
    REVOKED_LICENSE = 12
    ASKED_GROUP_MEMBERSHIP = 13
    NEW_GROUP_MEMBERSHIP = 14
    PROMOTED_GROUP_MEMBERSHIP = 15
    DOWNGRADED_GROUP_MEMBERSHIP = 16
    REMOVED_GROUP_MEMBERSHIP = 17
    REVOKED_GROUP_MEMBERSHIP_BY_ADMIN = 18
    CHANGED_GROUP_MAIN_ADMIN = 19


class People(Base):
    """ Class mapping SQL table People."""
    __tablename__ = 'people'
    id = Column(
        Integer,
        Sequence('people_seq', start=10000),
        primary_key=True)
    username = Column(Unicode(255), unique=True, nullable=False)
    password = Column(UnicodeText(), nullable=False)
    fullname = Column(UnicodeText(), nullable=False)
    ircnick = Column(UnicodeText(), unique=True, nullable=True)
    avatar = Column(UnicodeText(), nullable=True)
    avatar_id = Column(Unicode, nullable=True)
    introduction = Column(UnicodeText(), nullable=True)
    postal_address = Column(UnicodeText(), nullable=True)
    country_code = Column(Unicode(2), nullable=True)
    locale = Column(UnicodeText, default=u'en_US')
    birthday = Column(Integer(), nullable=True)
    birthday_month = Column(UnicodeText(), nullable=True)
    telephone = Column(UnicodeText(), nullable=True)
    facsimile = Column(UnicodeText(), nullable=True)
    affiliation = Column(UnicodeText(), nullable=True)
    bio = Column(UnicodeText(), nullable=True)
    timezone = Column(UnicodeText(), default=u'UTC')
    gpg_fingerprint = Column(UnicodeText(), nullable=True)
    ssh_key = Column(UnicodeText(), nullable=True)
    email = Column(UnicodeText(), unique=True, nullable=False)
    recovery_email = Column(UnicodeText(), unique=True, nullable=True)
    bugzilla_email = Column(UnicodeText(), unique=True, nullable=True)
    email_token = Column(UnicodeText(), unique=True, nullable=True)
    unverified_email = Column(UnicodeText(), nullable=True)
    security_question = Column(UnicodeText(), default=u'-')
    security_answer = Column(UnicodeText(), default=u'-')
    login_attempt = Column(Integer(), nullable=True)
    password_token = Column(UnicodeText(), nullable=True)
    old_password = Column(UnicodeText(), nullable=True)
    certificate_serial = Column(Integer, default=1)
    status = Column(Integer, default=AccountStatus.PENDING.value)
    status_timestamp = Column(UTCDateTime, default=func.current_timestamp())
    privacy = Column(Boolean, default=False)
    email_alias = Column(Boolean, default=True)
    blog_rss = Column(UnicodeText(), nullable=True)
    latitude = Column(Numeric, nullable=True)
    longitude = Column(Numeric, nullable=True)
    fas_token = Column(UnicodeText(), nullable=True)
    github_token = Column(UnicodeText(), nullable=True)
    twitter_token = Column(UnicodeText(), nullable=True)
    login_timestamp = Column(UTCDateTime, nullable=True)
    creation_timestamp = Column(
        UTCDateTime, nullable=False,
        default=func.current_timestamp()
    )
    update_timestamp = Column(
        UTCDateTime, nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    group_membership = relationship(
        'GroupMembership',
        foreign_keys='[GroupMembership.person_id]',
        backref=backref('person', lazy="joined"),
        cascade_backrefs=True
    )
    licenses = relationship(
        'SignedLicenseAgreement',
        order_by='SignedLicenseAgreement.id'
    )
    activities_log = relationship(
        'PeopleAccountActivitiesLog',
        order_by='PeopleAccountActivitiesLog.event_timestamp'
    )
    account_permissions = relationship(
        'AccountPermissions',
        primaryjoin='and_(AccountPermissions.person_id==People.id)',
        order_by='AccountPermissions.id'
    )

    __table_args__ = (
        Index('people_username_idx', username),
    )

    def get_status(self):
        """ Retrieves person's status definition and return it. """
        return AccountStatus[self.status]

    def get_created_date(self, request):
        """ Returns activity date in a translated human readable format. """
        return format_datetime(request.locale_name, self.creation_timestamp)

    def to_json(self, permissions):
        """ Returns a json/dict representation of this user.

        :param permissions: permission level to return related infos
        :type permissions: AccountPermissionType
        :return: A json/dict format of user's data
        :rtype: dict
        """
        info = OrderedDict()
        if permissions >= AccountPermissionType.CAN_READ_PUBLIC_INFO:
            # Standard public info
            info = {
                'id': self.id,
                'username': self.username,
                'fullname': self.fullname,
                'ircnick': self.ircnick,
                'avatar': self.avatar,
                'email': self.email,
                'creation_date': utc_iso_format(self.creation_timestamp),
                'status': self.status,
                'timezone': self.timezone,
                'gpg_fingerprint': self.gpg_fingerprint,
            }

        if permissions >= AccountPermissionType.CAN_READ_PEOPLE_FULL_INFO:
            info['countryCode'] = self.country_code
            info['locale'] = self.locale
            info['bugzilla_email'] = self.bugzilla_email or self.email
            info['blog_rss'] = self.blog_rss
            info['bio'] = self.bio

            if self.signed_license:
                info['license_agreement'] = [l.to_json() for l in self.licenses]

            info['membership'] = []
            if self.group_membership > 0:
                for groups in self.group_membership:
                    info['membership'].append(
                        {
                            'group_id': groups.group_id,
                            'group_name': groups.group.name,
                            'group_type': groups.group.group_type,
                            'sponsor_id': groups.sponsor_id,
                            'role': groups.role,
                            'status': groups.status,
                            'group_status': groups.group.status
                        }
                    )

            # Infos that people set as private
            if not self.privacy:
                info['email_alias'] = self.email_alias
                info['postal_address'] = self.postal_address
                info['telephone'] = self.telephone
                info['facsimile'] = self.facsimile
                info['affiliation'] = self.affiliation
                info['certificate_serial'] = self.certificate_serial
                info['ssh_key'] = self.ssh_key
                info['latitude'] = int(self.latitude or 0.0)
                info['longitude'] = int(self.longitude or 0.0)
                info['last_logged'] = utc_iso_format(self.login_timestamp)

                info['connected_applications'] = {
                    # 'fas': self.fas_token,
                    'github': 'connected' if self.github_token else 'inactivate',
                    'twitter': 'connected' if self.twitter_token else 'inactivate'
                }

                if self.account_permissions:
                    info['account_access'] = [
                        p.to_json() for p in self.account_permissions]

                if self.activities_log:
                    info['account_activities'] = [
                        log.to_json() for log in self.activities_log]
            else:
                info['privacy'] = self.privacy

        return info


class PeopleAccountActivitiesLog(Base):
    __tablename__ = 'people_activity_log'
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    location = Column(UnicodeText(), nullable=False)
    remote_ip = Column(Unicode, nullable=False)
    access_from = Column(UnicodeText(), nullable=False)
    event = Column(Integer, nullable=False)
    event_msg = Column(UnicodeText(), nullable=True)
    event_timestamp = Column(UTCDateTime, default=func.current_timestamp())

    person = relation('People', uselist=False)

    __table_args__ = (
        Index('account_access_log_idx', location),
        Index('people_access_log_idx', access_from),
    )

    def to_json(self):
        """
        Exports Account activities to JSON/dict format.

        :return: A dictionary of account's activities
        :rtype: dict
        """
        return {
            'location': self.location + ' (%s)' % self.remote_ip,
            'remote_client': self.access_from,
            'event': self.event,
            'timestamp': utc_iso_format(self.event_timestamp)
        }

    def get_date(self, request):
        """ Return activity date in a translated human readable format. """
        return format_datetime(request.locale_name, self.event_timestamp)


# class PeopleVirtualAccount(Base):
#     __tablename__ = 'virtual_people'
#     id = Column(Integer, unique=True, primary_key=True)
#     username = Column(UnicodeText(), unique=True, nullable=False)
#     parent = Column(Integer, ForeignKey('people.id'), nullable=False)
#     type = Column(Integer, default=1)
#     last_logged = Column(DateTime, default=datetime.datetime.utcnow)

