#!/usr/bin/python
# -*- mode: Python; indent-tabs-mode: nil; -*-

import errno, os, sys, stat
import re
import smtplib
import datetime, time
from optparse import OptionParser
import ConfigParser

from PackageOwners import PackageOwners
#from FakeOwners import FakeOwners as PackageOwners

FAS = {
    'project' : "Fedora EPEL",
    'user' : "",
    'passwd' : "",
    }

Mail = {
    'server' : "localhost",
    'user' : "",
    'passwd' : "",
    'maxsize' : 39*1024,
    'from' : "root@localhost",
    'replyto' : "root@localhost",
    'subject' : "Broken dependencies in EPEL",
}

class BrokenDep:
    def __init__(self):
        self.pkgid = None  # 'name - EVR.arch'
        self.repoid = None  # e.g. 'fedora-core-6-i386'
        self.srp_mname = None
        self.age = ''  # e.g. '(14 days)'
        self.owner = ''
        self.coowners = []
        # disabled/stripped feature
        self.mail = True  # whether to notify owner by mail
        # disabled/stripped feature
        self.new = False
        self.report = []

    def GetRequires(self):
        pkgid2 = self.pkgid.replace(' ','')
        r = []
        for line in self.report:
            if len(line) and not line.isspace() and not line.startswith('package: ') and line.find('unresolved deps:') < 0:
                r.append( '    '+pkgid2+'  requires  '+line.lstrip() )
        return '\n'.join(r)


def whiteListed(b): # Just a hook, not a generic white-list feature.
    # These two in Fedora 7 Everything most likely won't be fixed.
    if b.pkgid.startswith('kmod-em8300') and b.repoid.startswith('fedora-7'):
        return True
    elif b.pkgid.startswith('kmod-sysprof') and b.repoid.startswith('fedora-7'):
        return True
    elif b.pkgid.startswith('kmod'):  # gah ;)  temporarily catch them all
        return True
    else:
        return False


def makeOwners(brokendeps):
    owners = PackageOwners()
    try:
        #if not owners.FromURL():
        if not owners.FromURL(repoid=FAS['project'],username=FAS['user'],password=FAS['passwd']):
            raise IOError('ERROR: Could not retrieve package owner data.')
    except IOError, e:
        print e
        sys.exit(1)
    for b in brokendeps:
        toaddr = owners.GetOwner(b.srpm_name)
        if toaddr == '':
            toaddr = 'UNKNOWN OWNER'
            e = 'ERROR: "%s" not in owners.list!\n\n' % b.srpm_name
            if e not in errcache:
                errcache.append(e)
        b.owner = toaddr
        b.coowners = owners.GetCoOwnerList(b.srpm_name)


def mail(smtp, fromaddr, toaddrs, replytoaddr, subject, body):
    from email.Header import Header
    from email.MIMEText import MIMEText
    msg = MIMEText( body, 'plain' )
    from email.Utils import make_msgid
    msg['Message-Id'] = make_msgid()
    msg['Subject'] = Header(subject)
    msg['From'] = Header(fromaddr)
    from email.Utils import formatdate
    msg['Date'] = formatdate()
    if len(replytoaddr):
        msg['ReplyTo'] = Header(replytoaddr)

    if isinstance(toaddrs, basestring):
        toaddrs = [toaddrs]
    to = ''
    for t in toaddrs:
        if len(to):
            to += ', '
        to += t
    msg['To'] = Header(to)

    try:
        r = smtp.sendmail( fromaddr, toaddrs, msg.as_string(False) )
        for (name, errormsg) in r.iteritems():
            print name, ':', errormsg
    except smtplib.SMTPRecipientsRefused, obj:
        print 'ERROR: SMTPRecipientsRefused'
        for (addr, errormsg) in obj.recipients.iteritems():
            print addr, ':', errormsg
    except smtplib.SMTPException:
        print 'ERROR: SMTPException'


def mailsplit(smtp, fromaddr, toaddrs, replytoaddr, subject, body):
    # Split mail body at line positions to keep it below maxmailsize.
    parts = 0
    start = 0
    end = len(body)
    slices = []
    while ( start < end ):
        if ( (end-start) > Mail['maxsize'] ):
            nextstart = body.rfind( '\n', start, start+Mail['maxsize'] )
            if ( nextstart<0 or nextstart==start ):
                print 'ERROR: cannot split mail body cleanly'
                nextstart = end
        else:
            nextstart = end
        slices.append( (start, nextstart) )
        start = nextstart
        parts += 1

    curpart = 1
    for (start,end) in slices:
        if (parts>1):
            subjectmodified = ( '(%d/%d) %s' % (curpart, parts, subject) )
            time.sleep(1)
        else:
            subjectmodified = subject
        slicedbody = body[start:end]
        mail(smtp,fromaddr,toaddrs,replytoaddr,subjectmodified,slicedbody)
        curpart += 1


def loadConfigFile(filename):
    if not filename:
        return

    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(filename))
    except IOError, (e, errstr):
        print filename, ':', errstr
        sys.exit(e)
    
    try:
        if config.has_section('FAS'):
            for v in ['project','user','passwd']:
                if config.has_option('FAS',v):
                    FAS[v] = config.get('FAS',v)
        if config.has_section('Mail'):
            for v in ['server','user','passwd','from','replyto','subject']:
                if config.has_option('Mail',v):
                    Mail[v] = config.get('Mail',v)
                if config.has_option('Mail','maxsize'):
                    Mail['maxsize'] = config.getint('Mail','maxsize')

    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError), e:
        print 'Configuration file error:', e


### main

usage = "Usage: %s <options> <Extras repoclosure report file(s)>" % sys.argv[0]
parser = OptionParser(usage=usage)
parser.add_option("-c", "--config", default=None,
                  help="config file to use")
parser.add_option("-k", "--keyword", default=[], action='append',
                  help="a keyword to look for in repoids")
parser.add_option("-m", "--mail", default=[], action='append',
                  help="what mail to send (owner, summary)")
parser.add_option("-w", "--warn", default=[], action='append',
                  help="repository warnings to include (needsign, testing)")
parser.add_option("", "--noowners", default=False, action="store_true",
                  help="don't fetch package owner data from FAS")
(opts, args) = parser.parse_args()

loadConfigFile(opts.config)

domail = len(opts.mail)>0
brokendeps = []  # list of BrokenDeps
errcache = []  # error messages to be included in the summary mail

if not len(args):
    print usage
    sys.exit(errno.EINVAL)
# Parse extras-repoclosure output files and fill brokendeps array.
while len(args):
    logfilename = args[0]
    del args[0]

    f = file( logfilename )
    pkgre = re.compile('(?P<name>.*)-[^-]+-[^-]+$')
    inbody = False
    srcrpm = ''
    for line in f:
        if line.startswith('source rpm: '):
            w = line.rstrip().split(' ')
            srcrpm = w[2]
            res = pkgre.search( srcrpm )  # try to get src.rpm "name"
            if not res:  # only true for invalid input
                inbody = False
            else:
                srpm_name = res.group('name')
                inbody = True
            continue

        elif inbody and line.startswith('package: '):
            w = line.rstrip().split(' ')
            repoid = w[5]
            b = BrokenDep()
            b.pkgid = w[1]+' - '+w[3]  # name - EVR.arch
            b.repoid = repoid
            b.srpm_name = srpm_name
            brokendeps.append(b)

        if inbody:
            # Copy report per broken package.
            b.report.append( line.rstrip() )


def bdSortByOwnerAndName(a,b):
    return cmp(a.owner+a.pkgid,b.owner+b.pkgid)

def bdSortByRepoAndName(a,b):
    return cmp(a.repoid+a.pkgid,b.repoid+b.pkgid)


# Filter out unwanted repoids.
for b in list(brokendeps):
    for needle in opts.keyword:
        if b.repoid.find( needle ) >= 0:  # wanted?
            break
    else:
        brokendeps.remove(b)

# Filter out entries from whitelist.
for b in list(brokendeps):
    if whiteListed(b):
        brokendeps.remove(b)

# Fill in package owners.
if not opts.noowners:
    makeOwners(brokendeps)

# Build full mail report per owner. Use a flag for new breakage.
reports = {}  # map of lists [new,body] - a flag and the full report for a package owner
if not opts.noowners:
    brokendeps.sort(bdSortByOwnerAndName)
    for b in brokendeps:
        if b.new:
            print 'NEW breakage: %s in %s' % (b.pkgid, b.repoid)
        if b.mail:
            r = '\n'.join(b.report)+'\n'
            reports.setdefault(b.owner,[b.new,''])
            reports[b.owner][1] += r
            # Also build mails for co-owners.
            for toaddr in b.coowners:
                reports.setdefault(toaddr,[None,''])
                reports[toaddr][1] += r


sep = '='*70+'\n'
summail = ''  # main summary mail text
reportssummary = ''  # any NEW stuff for the summary

def giveNeedsignMsg():
    if 'needsign' in opts.warn:
        return sep+"The results in this summary consider unreleased updates in the\nbuild-system's needsign-queue!\n"+sep+'\n'
    else:
        return ''

def giveTestingMsg():
    if 'testing' in opts.warn:
        return sep+"The results in this summary consider Test Updates!\n"+sep+'\n'
    else:
        return ''

# Create summary mail text.
reportssummary += giveNeedsignMsg()
reportssummary += giveTestingMsg()
summail += reportssummary

if not opts.noowners and len(brokendeps):
    summail += ('Summary of broken packages (by owner):\n')
    brokendeps.sort(bdSortByOwnerAndName)
    o = None
    for b in brokendeps:
        if o != b.owner:
            o = b.owner
            seenbefore = []
            summail += '\n    '+b.owner.replace('@',' AT ')+'\n'
        if b.pkgid not in seenbefore:
            summail += '        '+b.pkgid+'    '+b.age+'\n'
            seenbefore.append(b.pkgid)

# Broken deps sorted by repository id.
brokendeps.sort(bdSortByRepoAndName)
r = None
for b in brokendeps:
    if r != b.repoid:
        r = b.repoid
        summail += '\n\n'+sep+('Broken packages in %s:\n\n' % b.repoid)
    summail += b.GetRequires()+'\n'

# Mail init.
if domail:
    srv = smtplib.SMTP( Mail['server'] )
    if ( len(Mail['user']) and len(Mail['passwd']) ):
        try:
            srv.login( Mail['user'], Mail['passwd'] )
        except smtplib.SMTPException:
            print 'ERROR: mailserver login failed'
            sys.exit(-1)

# Mail reports to owners.
for toaddr,(new,body) in reports.iteritems():
    # Send mail to every package owner with broken package dependencies.
    mailtext = 'Your following packages in the repository suffer from broken dependencies:\n\n'
    mailtext += giveNeedsignMsg()
    mailtext += giveTestingMsg()
    mailtext += body
    if domail and ('owners' in opts.mail) and toaddr!='UNKNOWN OWNER':
        subject = Mail['subject'] + ' - %s' % datetime.date.today()
        mail( srv, Mail['from'], toaddr, Mail['replyto'], subject, mailtext )

# Mail summary to mailing-list.
if domail and ('summary' in opts.mail):
    subject = Mail['subject'] + ' - %s' % datetime.date.today()
    toaddr = Mail['replyto']
    mailsplit( srv, Mail['from'], toaddr, '', subject, summail )

if domail:
    srv.quit()

if len(summail):
    print summail
