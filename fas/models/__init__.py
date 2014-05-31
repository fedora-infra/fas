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


#class AccountStatus(IntEnum):
#    ACTIVE = 1
#    INACTIVE = 3
#    LOCKED = 5
#    DISABLED = 8
class AccountStatus(Base):
    __tablename__ = 'account_status'
    id = sa.Column(sa.Integer, primary_key=True)
    status = sa.Column(sa.Unicode(50), unique=True, nullable=False)


#class RoleLevel(IntEnum):
#    UNKNOWN = 0
#    USER = 1
#    EDITOR = 2
#    SPONSOR = 3
#    ADMIN = 5
class RoleLevel(Base):
    __tablename__ = 'role_level'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(50), unique=True, nullable=False)

class AccountPermissionType(IntEnum):
    CAN_READ_PUBLIC_INFO = 0x01
    CAN_READ_PEOPLE_PUBLIC_INFO = 0x02
    CAN_READ_PEOPLE_FULL_INFO = 0x03
    CAN_READ_AND_EDIT_PEOPLE_INFO = 0x05
    CAN_EDIT_GROUP_INFO = 0x07

class AccountLogType(IntEnum):
    LOGGED_IN = 0x01
    ACCOUNT_UPDATE = 0x03
    APIKEY_REQUEST = 0x04