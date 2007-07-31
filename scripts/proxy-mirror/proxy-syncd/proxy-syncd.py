#!/usr/bin/python
import sys
import time
import sha
from urlgrabber.grabber import URLGrabber
from urlgrabber.grabber import URLGrabError

# original address
BASE1='http://gromit.redhat.com/pub/fedora/linux'
# proxy address
BASE2='http://download.boston.redhat.com/pub/fedora/linux'
# individual repos
DIRS="""
/updates/7/i386
/updates/testing/7/i386
/updates/7/x86_64
/updates/testing/7/x86_64
/updates/7/ppc
/updates/testing/7/x86_64
/development/i386/os
/development/x86_64/os
/development/ppc/os
/core/updates/6/i386
/core/updates/6/x86_64
/core/updates/6/ppc
"""
# All repodata files
REPOFILES=['repomd.xml','filelists.sqlite.bz2','filelists.xml.gz','other.sqlite.bz2','other.xml.gz','primary.sqlite.bz2','primary.xml.gz','updateinfo.xml.gz','comps.xml']
# Log File
LOGFILE='~/repodata-syncd.log'

DEBUG=False

# Hash URL, return hex sha1sum
# http_headers = (('Pragma', 'no-cache'),)
def hash_url(url):
    retval = ''
    try:
        f = g.urlopen(url)
        so = sha.new()
        so.update(f.read())
        f.close()
        retval = so.hexdigest()
    except URLGrabError:
        retval = 'ERROR: Try again later.'
    return retval
    
# Print Debug Messages
def debug(msg):
    if DEBUG == True:
        print "    DEBUG: %s" % msg

# Get Hashes of All repomd.xml
def hash_all_urls():
    for path in DIRDICT.keys():
        url = BASE1 + path + '/repodata/repomd.xml'
        hash = hash_url(url)
        DIRDICT[path] = hash
        print("%s %s" % (url, hash))

# Refresh Repodata
def refresh_repodata(path):
    url = BASE2 + path + '/repodata/'
    for file in REPOFILES:
        debug("Grabbing %s" % url + file)
        try:
            r.urlread(url + file)
        except URLGrabError:
            pass

### Main()
# Setup Variables
DIRLIST = DIRS.split()
tuples = []
for x in DIRLIST:
    if x.startswith('#') == False:
        tuples.append((x,0))
DIRDICT = dict(tuples)
g = URLGrabber(keepalive=0)
r = URLGrabber(keepalive=0,http_headers = (('Pragma', 'no-cache'),))

# Get Initial Hashes
hash_all_urls()
serial = 0

# Loop Forever
while True:
    print "serial=%d" % serial
    # Check each repodata directory
    for path in DIRDICT.keys():
        url  = BASE1 + path + '/repodata/repomd.xml'
        hash = hash_url(url)
        if hash != DIRDICT[path]:
            debug("CHANGE %s" % url)
            debug("       %s" % DIRDICT[path])
            debug("       %s" % hash)
            print 'REFRESHING ' + BASE2 + path
            # if hash changes, refresh repodata on proxy server
            refresh_repodata(path)
            # update dictionary entry to new hash value
            DIRDICT[path]=hash
    time.sleep(120)
    serial += 1
