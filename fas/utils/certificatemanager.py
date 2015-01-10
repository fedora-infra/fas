# -*- coding: utf-8 -*-
#
# Code based on pyOpenSSL's certgen.py example
#
# origin file:
# https://github.com/pyca/pyopenssl/blob/master/examples/certgen.py


from OpenSSL import crypto

class CertificateManager(object):

    __PEM__ = crypto.FILETYPE_PEM

    def __init__(self, cacert, cakey, config=None):
        self.cert = crypto.load_certificate(self.__PEM__, cacert)
        self.key = crypto.load_privatekey(self.__PEM__, cakey)
        self.pkey = None
        self.digest = config.get('openssl.cert.digest')
        self.bits = int(config.get('openssl.cert.bits'))
        self.key_type = int(config.get('openssl.cert.type'))
        self.config = config

    def __create_key_pair__(self):
        """
        Create a public/private key pair.
        """
        self.pkey = crypto.PKey()
        self.pkey.generate_key(self.key_type, self.bits)

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
        """
        self.__create_key_pair__()

        req = crypto.X509Req()
        subj = req.get_subject()

        if self.cert is None:
            for (key, value) in name.items():
                setattr(subj, key, value)
        else:
            csubj = self.cert.get_subject()
            client_desc = client_desc or csubj.organizationName
            setattr(subj, 'C', csubj.countryName)
            setattr(subj, 'ST', csubj.stateOrProvinceName)
            setattr(subj, 'L', csubj.localityName)
            setattr(subj, 'O', csubj.organizationName)
            setattr(subj, 'OU', client_desc)
            setattr(subj, 'CN', client_name)
            setattr(subj, 'emailAddress', client_email)

        req.set_pubkey(self.pkey)
        req.sign(self.pkey, self.digest)

        return req

    def create_client_certificate(self, cname, email, desc, serial):
        """
        Generate a client certificate
        :Arguments:
        :req:   Certificate reqeust to use
                   serial     - Serial number for the certificate
                   expire   - Timestamp (relative to now) when the certificate
                                stops being valid

        Returns:  tuple of generated certificate pub and priv key.
        """
        req = self.__create_cert_request__(cname, email, desc)

        cert = crypto.X509()
        cert.set_serial_number(serial)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(int(self.config.get('openssl.cert.expire')))
        cert.set_issuer(self.cert.get_subject())
        cert.set_subject(req.get_subject())
        cert.set_pubkey(req.get_pubkey())
        cert.sign(self.pkey, self.digest)

        return (
            crypto.dump_certificate(self.__PEM__, cert),
            crypto.dump_privatekey(self.__PEM__, self.pkey))

    def get_ca_cert(self):
        """ Returns certificate authority. """
        return self.cert

    def get_ca_key(self):
        """ Returns certificate authority private key. """
        return self.key

