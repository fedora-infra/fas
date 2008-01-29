#!/usr/bin/python

import os
import commands

dirs = ['/git/',
    '/hg/',
    '/svn/',
    '/bzr/',
    '/mtn/',]

for dir in dirs:
    projects = os.listdir(dir)
    for project in projects:
        path = "%s%s" % (dir, project)
        release = "/srv/web/releases/%s" % project
        if not os.path.islink(path):
            stat = os.lstat(path)
            print "%s %s" % (project, stat.st_gid)
            if not os.path.isdir(release):
                os.makedirs(release)
            if os.lstat(release).st_gid != stat.st_gid:
                os.chown(release, -1, stat.st_gid)
commands.getoutput('/usr/bin/find /srv/web/releases -type d | xargs /bin/chmod -R 2775')
