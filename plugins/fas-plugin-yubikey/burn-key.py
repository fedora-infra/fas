#!/usr/bin/python

# ykpersonalize -ofixed=ccccccccccci -afcaa0c5bf2e83ec040e4aeb7f8565293 -ouid=1e7f1da7d6d1
from fedora.client import AccountSystem, AuthError
from getpass import getpass, getuser
import subprocess, sys, gettext
from optparse import OptionParser

t = gettext.translation('fas', '/usr/share/locale', fallback = True)
_ = t.gettext

parser = OptionParser(version = "0.1")
parser.add_option('-u', '--username',
                  dest = 'username',
                  default = None,
                  metavar = 'username',
                  help = _('Fedora Account System username'))
parser.add_option('-U', '--url',
                  dest = 'url',
                  default = 'https://admin.fedoraproject.org/accounts/',
                  metavar = 'url',
                  help = _('FAS URL (Default: https://admin.fedoraproject.org/accounts/'))

(opts, args) = parser.parse_args()

if not opts.username:
    print _('Please provide a username.')
    parser.print_help()
    sys.exit(0)

if not getuser() == 'root':
    print _('''Please run this program as root as it will need to write
directly to the yubikey usb''')
    sys.exit(5)

print _(
'''
Attention: You are about to reprogram your yubikey!  Please ensure it is
plugged in to your USB slot before continuing.  The secret key currently on
your yubikey will be destroyed as part of this operation!

''')

print 'Contacting %s' % opts.url
password = getpass('Password for %s: ' % opts.username)

fas = AccountSystem(username=opts.username, password=password, base_url=opts.url)
try:
    new_key = fas.send_request('yubikey/genkey', auth=True)
except AuthError, e:
    print e
    sys.exit(1)

print
print _('New key generated in FAS, attempting to burn to yubikey')
print

opts = new_key['key'].split()

try:
    retcode = subprocess.call(['/usr/bin/ykpersonalize', 
                            '-ofixed=%s' % opts[0],
                            '-a%s' % opts[2],
                            '-ouid=%s' % opts[1]])
except KeyboardInterrupt:
    print _('''
Burn attempt cancelled by user!  Note: Even though the key did not get burned
onto your key, FAS did generate a new one.  This just means that if you did 
previously burn a different key, it will no longer work.
''')
    retcode=1

if retcode:
    print "There was an error writing to your yubi key"
else:
    print "Success!  Your Yubikey ID is %s" % opts[0]
