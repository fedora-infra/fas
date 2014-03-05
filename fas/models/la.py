from . import Base, AccountStatus

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


class LicenseAgreement(Base):
    __tablename__ = 'license_agreement'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    content = Column(UnicodeText(), nullable=False)
    comment = Column(UnicodeText(), nullable=True)
    creation_timestamp = Column(
                        DateTime,
                        nullable=False,
                        default=func.current_timestamp())
    update_timestamp = Column(
                        DateTime,
                        nullable=False,
                        default=func.current_timestamp())

    groups = relation(
                'Groups',
                foreign_keys='Groups.license_sign_up',
                primaryjoin='and_(LicenseAgreement.id==Groups.license_sign_up)',
                order_by='Groups.name'
    )


class SignedLicenseAgreement(Base):
    __tablename__ = 'signed_license_agreement'
    id = Column(Integer, primary_key=True)
    license = Column(Integer,
        ForeignKey('license_agreement.id'),
        primary_key=True)
    people = Column(Integer, ForeignKey('people.id'), primary_key=True)
    signed = Column(Boolean, nullable=False)

    licenses = relation('LicenseAgreement', order_by='LicenseAgreement.id')
