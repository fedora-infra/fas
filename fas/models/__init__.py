from flufl.enum import IntEnum
from sqlalchemy.ext.declarative import declarative_base

import sqlalchemy as sa
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class BaseStatus(IntEnum):
    INACTIVE = 0x00
    ACTIVE = 0x01
    PENDING = 0x03
    LOCKED = 0x05
    LOCKED_BY_ADMIN = 0x06
    DISABLED = 0x08

class AccountStatus(BaseStatus):
    ON_VACATION = 0x04

# Disable dynamic status as of right we don't handle workflow
# mechanism to manage new status adding by end-user.
#
# class AccountStatus(Base):
#    __tablename__ = 'account_status'
#    id = sa.Column(sa.Integer, primary_key=True)
#    status = sa.Column(sa.Unicode(50), unique=True, nullable=False)

class GroupStatus(BaseStatus):
    ARCHIVED = 0x0A

class MembershipStatus(IntEnum):
    UNAPPROVED = 0x00
    APPROVED = 0x01
    PENDING = 0x02

class LicenseAgreementStatus(IntEnum):
    DISABLED = 0x00
    ENABLED = 0x01

class MembershipRole(IntEnum):
    UNKNOWN = 0x00
    USER = 0x01
    EDITOR = 0x02
    SPONSOR = 0x03
    ADMINISTRATOR = 0x04

# Disable dynamic status as of right we don't handle workflow
# mechanism to manage new status adding by end-user.
#
# class RoleLevel(Base):
#    __tablename__ = 'role_level'
#    id = sa.Column(sa.Integer, primary_key=True)
#    name = sa.Column(sa.Unicode(50), unique=True, nullable=False)


class AccountPermissionType(IntEnum):
    CAN_READ_PUBLIC_INFO = 0x01
    CAN_READ_PEOPLE_PUBLIC_INFO = 0x02
    CAN_READ_PEOPLE_FULL_INFO = 0x03
    CAN_READ_AND_EDIT_PEOPLE_INFO = 0x05
    CAN_EDIT_GROUP_INFO = 0x07


class AccountLogType(IntEnum):
    LOGGED_IN = 0x01
    ACCOUNT_UPDATE = 0x03
    REQUESTED_API_KEY = 0x04
    UPDATE_PASSWORD = 0x05
    ASKED_RESET_PASSWORD = 0x06
    RESET_PASSWORD = 0x07
    SIGNED_LICENSE = 0x0A
    REVOKED_GROUP_MEMBERSHIP = 0x0B
    REVOKED_LICENSE = 0x0C
    ASKED_GROUP_MEMBERSHIP = 0x0D
    NEW_GROUP_MEMBERSHIP = 0x0E
