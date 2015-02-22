# -*- coding: utf-8 -*-
from . import Base

from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    UnicodeText,
    DateTime,
    Boolean,
    ForeignKey,
    func
    )

from sqlalchemy.orm import relation

from fas.models import AccountPermissionType

from fas.utils import format_datetime


class Plugins(Base):
    __tablename__ = 'plugins'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    comment = Column(UnicodeText(), nullable=True)
    enabled = Column(Boolean, nullable=False, default=False)


class AccountPermissions(Base):
    __tablename__ = 'account_permissions'
    id = Column(Integer, primary_key=True)
    people = Column(Integer, ForeignKey('people.id'), nullable=False)
    token = Column(UnicodeText(), unique=True, nullable=False)
    application = Column(UnicodeText(), nullable=False)
    permissions = Column(Integer, nullable=False)
    granted_timestamp = Column(
        DateTime, nullable=False,
        default=func.current_timestamp())
    last_used = Column(DateTime, nullable=True)

    account = relation('People', uselist=False)

    def get_granted_date(self, request):
        """ Return granted date of account perms in a translated
        human readable format.
        """
        return format_datetime(request.locale_name, self.granted_timestamp)

    def get_last_used_date(self, request):
        """ Return token last used date in a translated
         human readable format.
        """
        return format_datetime(request.locale_name, self.last_used)

    def get_perm_as_string(self):
        """ Return permission level as string format. """
        return AccountPermissionType(
            self.permissions
            ).name.lower().replace('_', ' ')


class TrustedPermissions(Base):
    __tablename__ = 'trusted_perms'
    id = Column(Integer, primary_key=True)
    application = Column(UnicodeText(), nullable=False)
    token = Column(UnicodeText(), nullable=False)
    secret = Column(UnicodeText(), nullable=False)
    permissions = Column(UnicodeText(), nullable=False)
    granted_timestamp = Column(
        DateTime, nullable=False,
        default=func.current_timestamp()
    )
    last_used = Column(DateTime, nullable=True)