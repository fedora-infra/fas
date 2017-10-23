# -*- coding: utf-8 -*-
#
# Copyright © 2016 Xavier Lamien.
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

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization

import datetime


class CertificateManager(object):

    def __init__(self, cacert, cakey, config=None):
        self.pkey = None
        self.cacert = x509.load_pem_x509_certificate(cacert, default_backend())
        self.cakey = rsa.RSABackend.load_rsa_private_numbers(cakey)
        self.digest = config.get('certificate.digest')
        self.bits = int(config.get('certificate.size'))
        self.key_type = int(config.get('certificate.type'))
        self.pub_exponent = int(config.get('certificate.public_exponent'))
        self.expiration_date = datetime.timedelta(
            seconds=int(self.config.get('certificate.expiry')))

    def __create_key_pair__(self):
        """
        Create a public/private key pair.
        """
        self.pkey = rsa.generate_private_key(self.pub_exponent, self.bits,
                                             default_backend())

    def __create_cert_request__(
            self, client_name, client_email, client_desc, **name):
        """
        Create a certificate request.

        :params **name: -
            The name of the subject of the request, possible
              arguments are:
              C     - Country name
              ST    - State or province name
              L     - Locality name
              O     - Organization name
              OU    - Organizational unit name
              CN    - Common name
              emailAddress - E-mail address
        :rtype: x509.Certificate
        """
        self.__create_key_pair__()

        csr = x509.CertificateSigningRequestBuilder()
        casubj = self.cacert.subject

        # if self.cacert is None:
        #     for (key, value) in name.items():
        #         setattr(subj, key, value)
        # else:
        #     csubj = self.cacert.subject
        #     client_desc = client_desc or csubj.organizationName
        #     setattr(subj, 'C', csubj.countryName)
        #     setattr(subj, 'ST', csubj.stateOrProvinceName)
        #     setattr(subj, 'L', csubj.localityName)
        #     setattr(subj, 'O', csubj.organizationName)
        #     setattr(subj, 'OU', client_desc)
        #     setattr(subj, 'CN', client_name)
        #     setattr(subj, 'emailAddress', client_email)

        csr = csr.subject_name(x509.Name(
            [
                casubj.get_attributes_for_oid(x509.NameOID.COUNTRY_NAME).pop(),
                casubj.get_attributes_for_oid(
                    x509.NameOID.STATE_OR_PROVINCE_NAME).pop(),
                casubj.get_attributes_for_oid(x509.NameOID.LOCALITY_NAME).pop(),
                casubj.get_attributes_for_oid(
                    x509.NameOID.ORGANIZATION_NAME).pop(),
                x509.NameAttribute(x509.NameOID.ORGANIZATIONAL_UNIT_NAME,
                                   client_desc),
                x509.NameAttribute(x509.NameOID.COMMON_NAME, client_name),
                x509.NameAttribute(x509.NameOID.EMAIL_ADDRESS, client_email)
            ]
        ))

        return csr.sign(self.pkey, hashes.SHA256(), default_backend())

    def create_client_certificate(self, cname, email, desc, serial):
        """
        Generate a client certificate
        :param cname: The client name
        :type cname: str
        :param email: The client email address
        :type email: str
        :param serial: A certificate serial number to set
        :type serial: int
        :param desc: The client description
        :type desc: str
        :returns:  Generated pub and priv key certificate.
        :rtype: tuple of bytes
        """
        csr = self.__create_cert_request__(cname, email, desc)

        cert = x509.CertificateBuilder()
        cert = cert.subject_name(csr.subject)
        cert = cert.issuer_name(self.cacert.subject)
        cert = cert.serial_number(serial)
        cert = cert.not_valid_before(datetime.datetime.now())
        cert = cert.not_valid_after(self.expiration_date)
        cert = cert.public_key(self.pkey.public_key())

        cert = cert.sign(self.pkey, hashes.SHA256(), default_backend())

        return cert.public_bytes(
            serialization.Encoding.PEM), self.pkey.private_bytes(
            serialization.Encoding.PEM)

    def get_ca_cert(self):
        """ Returns certificate authority. """
        return self.cacert

    def get_ca_key(self):
        """ Returns certificate authority private key. """
        return self.cakey
