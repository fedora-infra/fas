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
	# strip off the .git
	firstLetter = project[0]
	secondLetter = project[1]
        path = "%s%s" % (dir, project)
	releaseName = project.replace('.git', '')
        release = "/srv/web/releases/%s/%s/%s" % (firstLetter, secondLetter, releaseName)
        if not os.path.islink(path):
            stat = os.lstat(path)
            if not os.path.isdir(release):
                os.makedirs(release)
            if os.lstat(release).st_gid != stat.st_gid:
                os.chown(release, -1, stat.st_gid)
		os.chmod(release, 02775)
