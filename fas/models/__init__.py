from sqlalchemy.ext.declarative import declarative_base

import sqlalchemy as sa
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class AccountStatus(Base):
    __tablename__ = 'account_status'
    id = sa.Column(sa.Integer, primary_key=True)
    status = sa.Column(sa.Unicode(50), unique=True, nullable=False)


class RoleLevel(Base):
    __tablename__ = 'role_level'
    id = sa.Column(sa.Integer, primary_key=True)
    role = sa.Column(sa.Unicode(50), unique=True, nullable=False)
