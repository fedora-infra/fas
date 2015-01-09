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
    Index,
    func,
    )

from sqlalchemy.orm import relation


class Certificates(Base):

    __tablename__ = 'certificates'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText, nullable=True)
    cert = Column(UnicodeText(), nullable=False)
    cert_key = Column(UnicodeText(), nullable=False)
    client_cert_desc = Column(UnicodeText(), nullable=False)
    enabled = Column(Boolean(), default=False)
    creation_timestamp = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp()
    )

    __table_args__ = (
        Index('certificates_idx', id),
    )


class ClientsCertificates(Base):

    __tablename__ = 'clients_certificates'
    id = Column(Integer, primary_key=True)
    ca = Column(Integer, ForeignKey('certificates.id'))
    people = Column(Integer, ForeignKey('people.id'))
    serial = Column(Integer, default=1)
    certificate = Column(UnicodeText, nullable=True)

    cacert = relation(
        'Certificates',
        foreign_keys='Certificates.id',
        primaryjoin='and_(ClientsCertificates.ca==Certificates.id)')

    person = relation(
        'People',
        foreign_keys='People.id',
        primaryjoin='and_(ClientsCertificates.people==People.id)'
        )

