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

from babel.dates import format_date


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

    account = relation(
        'People',
        uselist=False
        )

    def get_granted_date(self, request):
        """ Return granted date of account perms in a translated
        human readable format.
        """
        date = self.granted_timestamp.date()

        return format_date(date, locale=request.locale_name)
