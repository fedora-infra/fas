# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Xavier Lamien.
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
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from . import Base, LicenseAgreementStatus
from fas.util import utc_iso_format
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
    """ Mapper class to SQL table LicenseAgreement. """
    __tablename__ = 'license_agreement'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    status = Column(Integer, default=LicenseAgreementStatus.DISABLED.value)
    content = Column(UnicodeText, nullable=False)
    comment = Column(UnicodeText, nullable=True)
    enabled_at_signup = Column(Boolean, default=False)
    creation_timestamp = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp()
    )
    update_timestamp = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp()
    )

    groups = relation(
        'Groups',
        foreign_keys='Groups.license_sign_up',
        primaryjoin='and_(LicenseAgreement.id==Groups.license_sign_up)',
        order_by='Groups.name'
    )

    def get_status(self):
        """

        :return:
        :rtype:
        """
        return LicenseAgreementStatus[self.status]

    def to_json(self):
        """
        Exports License Agreement to JSON/dict format.

        :return: A dictionary of LicenseAgreement's data
        :rtype: dict
        """
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'content': self.content,
            'comment': self.comment,
            'enabled_at_signup': self.enabled_at_signup,
            'created_on': utc_iso_format(self.creation_timestamp)
        }


class SignedLicenseAgreement(Base):
    """ Mapper class to SQL table SignedLicenseAgreement. """
    __tablename__ = 'signed_license_agreement'
    id = Column(Integer, primary_key=True)
    license = Column(
        Integer,
        ForeignKey('license_agreement.id')
        )
    people = Column(Integer, ForeignKey('people.id'))
    signed = Column(Boolean, nullable=False)

    licenses = relation(
        'LicenseAgreement',
        order_by='LicenseAgreement.id'
    )

    def to_json(self):
        """
        Exports License Agreement signing into JSON/dict format.

        :return: A dictionary of SignedLicenseAgreement's data.
        :rtype: dict
        """
        return {
            'name': self.license,
            'signed': self.signed
        }
