#!/usr/bin/python

# ykpersonalize -ofixed=ccccccccccci -afcaa0c5bf2e83ec040e4aeb7f8565293 -ouid=1e7f1da7d6d1
from fedora.client import AccountSystem, AuthError
from getpass import getpass
import subprocess, sys

username = raw_input("Username: ")
password = getpass('Password: ')
fas = AccountSystem(username=username, password=password, base_url='http://ipa.mmcgrath.net:8088/accounts/')
try:
    new_key = fas.send_request('yubikey/genkey', auth=True)
except AuthError, e:
    print e
    sys.exit(1)
opts = new_key['key'].split()

retcode = subprocess.call(['/usr/bin/ykpersonalize', 
                            '-ofixed=%s' % opts[0],
                            '-a%s' % opts[2],
                            '-ouid=%s' % opts[1]])

#cmd = subprocess.Popen(['/usr/bin/ykpersonalize', 
#                            '-ofixed=%s' % opts[0],
#                            '-a%s' % opts[2],
#                            '-ouid=%s' % opts[1]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#(stdout_data, stderr_data) = cmd.communicate(stdin)

if retcode:
    print "There was an error writing to your yubi key"
else:
    print "Success!  Your Yubikey ID is %s" % opts[0]
