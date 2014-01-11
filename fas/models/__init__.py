from flufl.enum import IntEnum
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class AccountStatus(IntEnum):
    ACTIVE = 1
    INACTIVE = 3
    BLOCKED = 5
    DISABLED = 8

class RoleLevel(IntEnum):
    UNKNOWN = 0
    USER = 1
    EDITOR = 2
    SPONSOR = 3
    ADMIN = 5
