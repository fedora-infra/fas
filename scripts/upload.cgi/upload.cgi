#!/usr/bin/python
#
# CGI script to handle file updates for the rpms CVS repository. There
# is nothing really complex here other than tedious checking of our
# every step along the way...
#
# $Id: upload.cgi,v 1.10 2005/04/15 23:44:24 gafton Exp $
# License: GPL

import os
import sys
import cgi
import stat
import md5
import tempfile
import StringIO

sys.path.append('/var/fedora-accounts')
import website

# reading buffer size
BUFFER_SIZE = 4096

# Debugging version
DEBUG = 0

# We check modules exist from this dircetory
CVSREPO = "/cvs/pkgs/rpms"

do_userdb_auth = 1

# log a trace of what we're doing
def log_msg(*msgs):
    s = StringIO.StringIO()
    for m in msgs:
        s.write("%s " % (m,))
    sys.stderr.write("%s\n" % (s.getvalue(),))
    del s

os.umask(002)

# log the entire environment
def log_environ():
    for k in os.environ.keys():
        log_msg("%s=%s" % (k, os.environ[k]))
    return

# abort running the script
def send_error(text):
    print "Content-type: text/plain\n"
    print text
    sys.exit(1)

# prepare to exit graciously
def send_ok(text):
    print "Content-type: text/plain\n"
    if text:
        print text

# check and validate that all the fields are present
def check_form(var):
    if not form.has_key(var):
	send_error("required field '%s' is not present" % (var,))
    ret = form.getvalue(var)
    if type(ret) == type([]):
        send_error("Multiple values given for '%s'. Aborting" % (var,))
    ret = os.path.basename(ret) # this is a path component
    return ret

# if a directory exists, check that it has the proper permissions
def check_dir(tmpdir, wok = os.W_OK):
    if not os.access(tmpdir, os.F_OK):
        return 0
    if not os.access(tmpdir, os.R_OK|os.X_OK|wok):
        send_error("Unable to write to %s repository." % (
            tmpdir,))
    if not os.path.isdir(tmpdir):
        send_error("Path %s is not a directory." % (tmpdir,))
    return 1

#
# MAIN START
#
if do_userdb_auth:
    dbh = website.get_dbh()
auth_username = auth_password = None
need_auth = 1
if os.environ.has_key('SSL_CLIENT_S_DN_CN'):
    auth_username = os.environ['SSL_CLIENT_S_DN_CN']
    need_auth = 0
elif do_userdb_auth and 0:
    authtype, authinfo = website.get_http_auth_info()

    need_auth = 1
    auth_msg = "Authentication is required."

    if authinfo:
        if authtype.lower() == 'basic':
            need_auth = not website.do_checkpass(dbh, authinfo[0], authinfo[1])
	    auth_username, auth_password = authinfo
            auth_msg = "Username or password incorrect."
        else:
            auth_msg = "Unknown authentication type %s" % authtype

pieces = os.environ['REQUEST_URI'].split('/')
assert pieces[1] == 'repo'
if do_userdb_auth:
    #need_auth = need_auth or not website.have_group(dbh, auth_username, 'cvs' + pieces[2])
    need_auth = need_auth or not website.have_group(dbh, auth_username, 'cvsextras')
auth_msg = "You do not have the appropriate authorization to upload. %s %s %s" % (dbh, auth_username, 'cvs' + pieces[2])

if need_auth:
        print """Status: 403 Unauthorized to access the document
WWW-authenticate: Basic realm="fedora.redhat.com"
Content-type: text/plain

""" + str(auth_msg)
        sys.exit(0)

form = cgi.FieldStorage()
NAME = check_form("name")
MD5SUM = check_form("md5sum")

# Is this a submission or a test?
# in a test, we don't get a FILE, just a FILENAME.
# In a submission, we don;t get a FILENAME, just the FILE.
FILE = None
FILENAME = None
if form.has_key("filename"):
    # check the presence of the file
    FILENAME = check_form("filename")   
    log_msg("Checking file status",
            "NAME=%s FILENAME=%s MD5SUM=%s" % (NAME,FILENAME,MD5SUM))
else:
    if form.has_key("file"):
        FILE = form["file"]
        if not FILE.file:
            send_error("No file given for upload. Aborting")
        try:
            FILENAME = os.path.basename(FILE.filename)
        except:
            send_error("Could not extract the filename for upload. Aborting")
    else:
        send_error("required field '%s' is not present" % ("file", ))
        log_msg("Processing upload request",
                "NAME=%s FILENAME=%s MD5SUM=%s" % (NAME,FILENAME,MD5SUM))
# Now that all the fields are valid,, figure out our operating environment
if not os.environ.has_key("SCRIPT_FILENAME"):
    send_error("My running environment is funky. Aborting")

# start processing this request
my_script = os.environ["SCRIPT_FILENAME"]
# the module's top level directory
my_topdir = os.path.dirname(my_script)
my_moddir = "%s/%s" % (my_topdir, NAME)
my_filedir = "%s/%s" % (my_moddir, FILENAME)
my_md5dir =  "%s/%s" % (my_filedir, MD5SUM)

# first test if the module really exists
if not check_dir("%s/%s" % (CVSREPO, NAME), 0):
    log_msg("Unknown module", NAME)
    send_ok("Module '%s' does not exist!" % (NAME,))
    sys.exit(-9)
    
# try to see if we already have this file...
file_dest = "%s/%s/%s/%s/%s" % (my_topdir, NAME, FILENAME, MD5SUM, FILENAME)
if os.access(file_dest, os.F_OK | os.R_OK):
    # already there, spare the effort
    s = os.stat(file_dest)    
    # if we're just checking we need to be rather terse
    if FILE is None:
        message = "Available"
    else:
        FILE.file.close()
        message = "File %s already exists\nFile: %s Size: %d" % (
            FILENAME, file_dest, s[stat.ST_SIZE])
    send_ok(message)
    sys.exit(0)
# just checking?
if FILE is None:
    send_ok("Missing")
    sys.exit(-9)
    
# check that all directories are in place
for tmpdir in [ my_topdir, my_moddir, my_filedir, my_md5dir]:
    if not check_dir(tmpdir):
        # we agree to create this directory if the corresponding cvs module dir exists
        if tmpdir == my_moddir:
            # W_OK access is not necessary for this cgi
            if check_dir("%s/%s" % (CVSREPO, NAME), 0):
                os.mkdir(tmpdir, 02775)
                log_msg("mkdir", tmpdir)
                continue
        if tmpdir in [ my_filedir, my_md5dir ]:
            # don't require those directories just yet
            continue
        send_error("Directory %s does not exist and I won't create it" % (tmpdir,))
        
# grab a temporary filename and dump our file in there
tempfile.tempdir = my_moddir
tmpfile = tempfile.mktemp(MD5SUM)
tmpfd = open(tmpfile, "wb+")
# now read the whole file in
m = md5.new()
FILELENGTH=0
while 1:
    s = FILE.file.read(BUFFER_SIZE)
    if not s:
    	break
    tmpfd.write(s)
    m.update(s)
    FILELENGTH = FILELENGTH + len(s)
# now we're done reading, check the MD5 sum of what we got
tmpfd.close()
my_md5sum = m.hexdigest()
if MD5SUM != my_md5sum:
    send_error("MD5 check failed. Received %s instead of %s" % (
        my_md5sum, MD5SUM))
# wow, even the MD5SUM matches. make sure full path is valid now
for tmpdir in [ my_moddir, my_filedir, my_md5dir ]:
    if not check_dir(tmpdir):
        os.mkdir(tmpdir, 02775)
        log_msg("mkdir", tmpdir)
# and move our file to the final location
os.rename(tmpfile, file_dest)
log_msg("Stored filesize", FILELENGTH, file_dest)

send_ok("File %s size %d MD5 %s stored OK" % (FILENAME, FILELENGTH, MD5SUM))
