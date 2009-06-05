# Pretty much all copied from pyOpenSSL's certgen.py example and func's certs.py
# func's certs.py is GPLv2+
# pyOpenSSL is LGPL (Probably v2+)
# The pyOpenSSL examples may be under the same license but I'm not certain.

from OpenSSL import crypto
import subprocess

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

def create_key(key_type, bits):
    """
    Create a public/private key pair.

    Arguments: key_type - Key type, must be one of TYPE_RSA and TYPE_DSA
               bits - Number of bits to use in the key
    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(key_type, bits)
    return pkey

def create_csr(pkey, digest="md5", **name):
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

def revert_all_certs(person, config):
    indexfile = open(config.get('openssl_ca_index'))
    for entry in indexfile:
        attrs = entry.split('\t')
        if attrs[0] != 'V':
            continue
        # the index line looks something like this:
        # R\t090816180424Z\t080816190734Z\t01\tunknown\t/C=US/ST=Pennsylvania/O=Fedora/CN=test1/emailAddress=rickyz@cmu.edu
        # V\t090818174940Z\t\t01\tunknown\t/C=US/ST=North Carolina/O=Fedora Project/OU=Upload Files/CN=toshio/emailAddress=badger@clingman.lan
        dn = attrs[5]
        serial = attrs[3]
        info = {}
        for pair in dn.split('/'):
            if pair:
                key, value = pair.split('=')
                info[key] = value
        if info['CN'] == person.username:
            # revoke old certs
            subprocess.call([config.get('makeexec'), '-C',
                config.get('openssl_ca_dir'), 'revoke',
                'cert=%s/%s' % (config.get('openssl_ca_newcerts'), serial + '.pem')])

def sign_cert(reqfile, certfile, config):
    command = [config.get('makeexec'), '-C', config.get('openssl_ca_dir'),
            'sign', 'req=%s' % reqfile, 'cert=%s' % certfile]
    return subprocess.call(command)

def lock_ca(config):
    while True:
        try:
            os.mkdir(os.path.join(config.get('openssl_lockdir'), 'lock'))
            break
        except OSError:
            time.sleep(0.75)

def unlock_ca(config):
    os.rmdir(os.path.join(config.get('openssl_lockdir'), 'lock'))

