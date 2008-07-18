# Pretty much all copied from pyOpenSSL's certgen.py example and func's certs.py
# func's certs.py is GPLv2+
# pyOpenSSL is LGPL (Probably v2+)
# The pyOpenSSL examples may be under the same license but I'm not certain.

from OpenSSL import crypto
TYPE_RSA = crypto.TYPE_RSA
TYPE_DSA = crypto.TYPE_DSA

def retrieve_key_from_file(keyfile):
    fo = open(keyfile, 'r')
    buf = fo.read()
    keypair = crypto.load_privatekey(crypto.FILETYPE_PEM, buf)
    return keypair

def retrieve_cert_from_file(certfile):
    fo = open(certfile, 'r')
    buf = fo.read()
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, buf)
    return cert

def createKeyPair(key_type, bits):
    """
    Create a public/private key pair.

    Arguments: key_type - Key type, must be one of TYPE_RSA and TYPE_DSA
               bits - Number of bits to use in the key
    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(key_type, bits)
    return pkey

def createCertRequest(pkey, digest="md5", **name):
    """
    Create a certificate request.

    Arguments: pkey   - The key to associate with the request
               digest - Digestion method to use for signing, default is md5
               **name - The name of the subject of the request, possible
                        arguments are:
                          C     - Country name
                          ST    - State or province name
                          L     - Locality name
                          O     - Organization name
                          OU    - Organizational unit name
                          CN    - Common name
                          emailAddress - E-mail address
    Returns:   The certificate request in an X509Req object
    """
    req = crypto.X509Req()
    subj = req.get_subject()

    for (key,value) in name.items():
        setattr(subj, key, value)

    req.set_pubkey(pkey)
    req.sign(pkey, digest)
    return req

def createCertificate(req, (issuerCert, issuerKey), serial, (notBefore, notAfter), digest="md5"):
    """
    Generate a certificate given a certificate request.

    Arguments: req        - Certificate reqeust to use
               issuerCert - The certificate of the issuer
               issuerKey  - The private key of the issuer
               serial     - Serial number for the certificate
               notBefore  - Timestamp (relative to now) when the certificate
                            starts being valid
               notAfter   - Timestamp (relative to now) when the certificate
                            stops being valid
               digest     - Digest method to use for signing, default is md5
    Returns:   The signed certificate in an X509 object
    """
    cert = crypto.X509()
    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(notBefore)
    cert.gmtime_adj_notAfter(notAfter)
    cert.set_issuer(issuerCert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuerKey, digest)
    return cert

