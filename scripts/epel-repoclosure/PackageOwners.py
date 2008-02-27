#!/usr/bin/python
# -*- mode: Python; indent-tabs-mode: nil; -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import commands
import errno
import os, sys, time
import shutil
import tempfile
from urllib import FancyURLopener


class AccountsURLopener(FancyURLopener):
    """Subclass of urllib.FancyURLopener to allow passing http basic auth info"""
    def __init__(self, username, password):
        FancyURLopener.__init__(self)
        self.username = username
        self.password = password

    def prompt_user_passwd(self, host, realm):
        return (self.username, self.password)


class PackageOwners:
    """interface to Fedora package owners list (and Fedora Extras owners/owners.list file)"""

    def __init__(self):
        self.dict = {}
        self.how = 'unknown'


    def FromURL(self, retries=3, retrysecs=300, url='https://admin.fedoraproject.org/pkgdb/acls/bugzilla?tg_format=plain',
                pkgdb=True, repoid='Fedora', username=None, password=None):
        # old url='http://cvs.fedora.redhat.com/viewcvs/*checkout*/owners/owners.list?root=extras'
        if pkgdb:
            self.how = 'pkgdb'
        else:
            self.how = 'url'
        self.url = url
        self.repoid = repoid
        self.retries = retries
        self.retrysecs = retrysecs
        self.username = username
        self.password = password
        return self._refresh()


    def FromCVS(self, retries=3, retrysecs=300, command='LC_ALL=C CVS_RSH=ssh cvs -f -d :pserver:anonymous@cvs.fedora.redhat.com:/cvs/extras co owners', workdir='',repoid='Fedora'):
        self.how = 'cvs'
        self.command = command
        self.repoid = repoid
        self.retries = retries
        self.retrysecs = retrysecs
        self.workdir = workdir
        self.ownersfile = os.path.join('owners', 'owners.list')
        self.cwdstack = []
        return self._refresh()


    def __getitem__(self,rpmname):
        """return e-mail address from initialowner field"""
        return self.GetOwner(rpmname)


    def GetOwner(self,rpmname):
        """return e-mail address from initialowner field"""
        try:
            r = self.dict[rpmname]['mailto']
        except KeyError:
            r = ''
        return r


    def GetOwners(self,rpmname):
        """return list of e-mail addresses from initialowner+initialcclist fields"""
        r = self.GetCoOwnerList(rpmname)
        r2 = self.GetOwner(rpmname)
        if len(r2):
            r.append(r2)
        return r


    def GetCoOwnerList(self,rpmname):
        """return list of e-mail addresses from initialcclist field"""
        try:
            r = self.dict[rpmname]['cc']
        except KeyError:
            r = []
        return r


    def _enterworkdir(self):
        self.cwdstack.append( os.getcwd() )
        if self.workdir != '':
            os.chdir(self.workdir)


    def _leaveworkdir(self):
        if len(self.cwdstack):
            os.chdir( self.cwdstack.pop() )


    def _refresh(self):
        self.dict = {}  # map package name to email address, dict[name]
        return self._download()


    def _parse(self,ownerslist):
        for line in ownerslist:
            if line.startswith('#') or line.isspace():
                continue
            try:
                (repo,pkgname,summary,emails,qacontact,cc) = line.rstrip().split('|')
                # This is commented, because we don't need the summary.
                #summary.replace(r'\u007c','|').replace('\u005c','\\')

                # The PkgDb includes repo's other than Fedora (Fedora EPEL,
                # Fedora OLPC, and Red Hat Linux, for example).  Skip them.
                if repo != self.repoid:
                    continue
                def fixaddr(a):
                    # Old Fedora CVS owners.list contains e-mail addresses.
                    # PkgDb plain output contains usernames only.
                    if not self.how == 'pkgdb':
                        return a
                    if not self.usermap.has_key(a):
                        return a
                    return self.usermap[a]

                addrs = []
                mailto = '' # primary pkg owner
                if len(emails):
                    if emails.find(',')>=0:
                        (addrs) = emails.split(',')
                        mailto = addrs[0]
                        addrs = addrs[1:]
                    else:
                        mailto = emails
                    mailto = fixaddr(mailto)

                ccaddrs = []
                if len(cc):
                    (ccaddrs) = cc.split(',')
                addrs += ccaddrs
                addrs = map(lambda a: fixaddr(a), addrs)

                self.dict[pkgname] = {
                    'mailto' : mailto,
                    'cc' : addrs
                    }
            except:
                print 'ERROR: owners.list is broken'
                print line


    def _downloadfromcvs(self):
        self._enterworkdir()
        # Dumb caching. Check that file exists and is "quite recent".
        cached = False
        try:
            fstats = os.stat(self.ownersfile)
            if ( fstats.st_size and
                 ((time.time() - fstats.st_ctime) < 3600*2) ):
                cached = True
        except OSError:
            pass

        if not cached:
            # Remove 'owners' directory contents, if it exists.
            for root, dirs, files in os.walk( 'owners', topdown=False ):
                for fname in files:
                    os.remove(os.path.join( root, fname ))
                for dname in dirs:
                    os.rmdir(os.path.join( root, dname ))
            # Retry CVS checkout a few times.
            for count in range(self.retries):
                (rc, rv) = commands.getstatusoutput(self.command)
                if not rc:
                    break
                print rv
                time.sleep(self.retrysecs)
            if rc:
                # TODO: customise behaviour on error conditions
                self._leaveworkdir()
                return False

        try:
            f = file( self.ownersfile )
        except IOError, (err, strerr):
            print 'ERROR: %s' % strerr
            # TODO: customise behaviour on error conditions
            self._leaveworkdir()
            return err
        ownerslist = f.readlines()
        f.close()
        self._parse(ownerslist)
        self._leaveworkdir()
        return True


    def _getlinesfromurl(self,url):
        err = 0
        strerr = ''
        # Retry URL download a few times.
        for count in range(self.retries):
            if count != 0:
                time.sleep(self.retrysecs)
            try:
                opener = AccountsURLopener(self.username, self.password)
                f = opener.open(url)
                rc = 0
                if 'www-authenticate' in f.headers:
                    rc = 1
                    strerr = 'Authentication is required to access %s' % url
                break
            except IOError, (_err, _strerr):
                rc = 1
                print url
                print _strerr
                (err,strerr) = (_err,_strerr)
        if rc:
            raise IOError, (err, strerr)
        else:
            l = f.readlines()
            f.close()
            return l


    def _downloadfromurl(self):
        self._parse(self._getlinesfromurl(self.url))
        return True


    def _downloadfrompkgdb(self):
        fasdump = self._getlinesfromurl('https://admin.fedoraproject.org/accounts/dump-group.cgi')
        self.usermap = {}
        for line in fasdump:
            fields = line.split(',')
            try:
                user = fields[0]
                addr = fields[1]
            except IndexError:
                print line
                raise
            if (addr.find('@') < 0):  # unexpected, no addr
                print 'No email in:', line
                raise Exception
            self.usermap[user] = addr
        self._parse(self._getlinesfromurl(self.url))
        return True


    def _download(self):
        if self.how == 'url':
            return self._downloadfromurl()
        elif self.how == 'pkgdb':
            return self._downloadfrompkgdb()
        elif self.how == 'cvs':
            return self._downloadfromcvs()
        else:
            self.__init__()
            return False


