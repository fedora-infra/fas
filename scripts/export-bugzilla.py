#!/usr/bin/python -t
__requires__ = 'TurboGears'
import pkg_resources
pkg_resources.require('CherryPy >= 2.0, < 3.0alpha')

import sys
import getopt
import xmlrpclib
import turbogears
import bugzilla
from turbogears import config
turbogears.update_config(configfile="/etc/export-bugzilla.cfg")
from turbogears.database import session
from fas.model import BugzillaQueue

BZSERVER = config.get('bugzilla.url', 'https://bugdev.devel.redhat.com/bugzilla-cvs/xmlrpc.cgi')
BZUSER = config.get('bugzilla.username')
BZPASS = config.get('bugzilla.password')

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], '', ('usage', 'help'))
    if len(args) != 2 or ('--usage','') in opts or ('--help','') in opts:
        print """
    Usage: export-bugzilla.py GROUP BUGZILLA_GROUP
    """
        sys.exit(1)
    ourGroup = args[0]
    bzGroup = args[1]

    server = bugzilla.Bugzilla(url=BZSERVER, user=BZUSER, password=BZPASS)
    bugzilla_queue = BugzillaQueue.query.join('group').filter_by(
            name=ourGroup)

    for entry in bugzilla_queue:
        # Make sure we have a record for this user in bugzilla
        if entry.action == 'r':
            # Remove the user's bugzilla group
            try:
                server.updateperms(entry.email, 'rem', (bzGroup,))
            except xmlrpclib.Fault, e:
                if e.faultCode == 504:
                    # It's okay, not having this user is equivalent to setting
                    # them to not have this group.
                    pass
                else:
                    raise

        elif entry.action == 'a':
            # Try to create the user
            try:
                server.adduser(entry.email, entry.person.human_name)
            except xmlrpclib.Fault, e:
                if e.faultCode == 500:
                    # It's okay, we just need to make sure the user has an
                    # account.
                    pass
                else:
                    print entry.email,entry.person.human_name
                    raise
            server.updateperms(entry.email, 'add', (bzGroup,))
        else:
            print 'Unrecognized action code: %s %s %s %s %s' % (entry.action,
                    entry.email, entry.person.human_name, entry.person.username, entry.group.name)
        
        # Remove them from the queue
        session.delete(entry)
        session.flush()
