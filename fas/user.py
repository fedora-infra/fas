import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler, config
from turbogears.database import session
import cherrypy

import os
import re
import gpgme
import StringIO
import crypt
import random
import subprocess

from fas.model import People
from fas.model import PersonEmails
from fas.model import Log

from fas.auth import *

from random import Random
import sha
from base64 import b64encode


class KnownUser(validators.FancyValidator):
    '''Make sure that a user already exists'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        try:
            p = People.by_username(value)
        except InvalidRequestError:
            raise validators.Invalid(_("'%s' does not exist.") % value, value, state)

class NonFedoraEmail(validators.FancyValidator):
    '''Make sure that an email address is not @fedoraproject.org'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        if value.endswith('@fedoraproject.org'):
            raise validators.Invalid(_("To prevent email loops, your email address cannot be @fedoraproject.org."), value, state)

class UnknownUser(validators.FancyValidator):
    '''Make sure that a user doesn't already exist'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        try:
            p = People.by_username(value)
        except InvalidRequestError:
            return
        except:
            raise validators.Invalid(_("Error: Could not create - '%s'") % value, value, state)

        raise validators.Invalid(_("'%s' already exists.") % value, value, state)

class ValidUsername(validators.FancyValidator):
    '''Make sure that a username isn't blacklisted'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        username_blacklist = config.get('username_blacklist')
        if re.compile(username_blacklist).match(value):
          raise validators.Invalid(_("'%s' is an illegal username.") % value, value, state)

class UserSave(validators.Schema):
    targetname = KnownUser
    human_name = validators.All(
        validators.String(not_empty=True, max=42),
        validators.Regex(regex='^[^\n:<>]+$'),
        )
    #mail = validators.All(
    #    validators.Email(not_empty=True, strip=True, max=128),
    #    NonFedoraEmail(not_empty=True, strip=True, max=128),
    #)
    #fedoraPersonBugzillaMail = validators.Email(strip=True, max=128)
    #fedoraPersonKeyId- Save this one for later :)
    postal_address = validators.String(max=512)

class UserCreate(validators.Schema):
    username = validators.All(
        UnknownUser,
        ValidUsername(not_empty=True),
        validators.String(max=32, min=3),
        validators.Regex(regex='^[a-z][a-z0-9]+$'),
    )
    human_name = validators.All(
        validators.String(not_empty=True, max=42),
        validators.Regex(regex='^[^\n:<>]+$'),
        )
    email = validators.All(
        validators.Email(not_empty=True, strip=True),
        NonFedoraEmail(not_empty=True, strip=True),
    )
    #fedoraPersonBugzillaMail = validators.Email(strip=True)
    postal_address = validators.String(max=512)

class UserSetPassword(validators.Schema):
    currentpassword = validators.String
    # TODO (after we're done with most testing): Add complexity requirements?
    password = validators.String(min=8)
    passwordcheck = validators.String
    chained_validators = [validators.FieldsMatch('password', 'passwordcheck')]

class UserView(validators.Schema):
    username = KnownUser

class UserEdit(validators.Schema):
    targetname = KnownUser

def generate_password(password=None, length=14):
    ''' Generate Password '''
    secret = {} # contains both hash and password

    if not password:
        # Exclude 1,l and 0,O
        chars = '23456789abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNPQRSTUVWXYZ'
        password = ''
        for i in xrange(length):
            password += random.choice(chars)

    secret['hash'] = crypt.crypt(password, "$1$%s" % generate_salt(8))
    secret['pass'] = password

    return secret

def generate_salt(length=8):
    chars = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    salt = ''
    for i in xrange(length):
        salt += random.choice(chars)
    return salt

class User(controllers.Controller):

    def __init__(self):
        '''Create a User Controller.
        '''

    @identity.require(turbogears.identity.not_anonymous())
    def index(self):
        '''Redirect to view
        '''
        turbogears.redirect('/user/view/%s' % turbogears.identity.current.user_name)

    def jsonRequest(self):
        return 'tg_format' in cherrypy.request.params and \
                cherrypy.request.params['tg_format'] == 'json'


    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=UserView())
    @error_handler(error)
    @expose(template="fas.templates.user.view", allow_json=True)
    def view(self, username=None):
        '''View a User.
        '''
        if not username:
            username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if turbogears.identity.current.user_name == username:
            personal = True
        else:
            personal = False
        if isAdmin(person):
            admin = True
        else:
            admin = False
        groups = []
        # Possibly extract this info in view (person.roles[n].group gives the group)
        for group in person.roles:
            groups.append(Groups.by_name(group.group.name))
        cla = None
        if clickedCLAPrivs(person):
            cla = 'clicked'
        if signedCLAPrivs(person):
            cla = 'signed'
        person.jsonProps = {
                'People': ('approved_memberships', 'unapproved_memberships')
                }
        return dict(person=person, cla=cla, personal=personal, admin=admin)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=UserEdit())
    @error_handler(error)
    @expose(template="fas.templates.user.edit")
    def edit(self, targetname=None):
        '''Edit a user
        '''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        if targetname:
            target = People.by_username(targetname)
        else:
            target = person
        if not canEditUser(person, target):
            turbogears.flash(_('You cannot edit %s') % target.username )
            username = turbogears.identity.current.username
        return dict(target=target)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=UserSave())
    @error_handler(error)
    @expose(template='fas.templates.user.edit')
    def save(self, targetname, human_name, telephone, postal_address, email, ircnick=None, gpg_keyid=None, comments='', locale='en', timezone='UTC'):
        username = turbogears.identity.current.user_name
        target = targetname
        person = People.by_username(username)
        target = People.by_username(target)

        if not canEditUser(person, target):
            turbogears.flash(_("You do not have permission to edit '%s'" % target.username))
            turbogears.redirect('/user/edit/%s', target.username)
            return dict()
        try:
            target.human_name = human_name
            target.emails['primary'].email = email
#            target.emails['bugzilla'] = PersonEmails(primary=bugzilla)
            target.ircnick = ircnick
            target.gpg_keyid = gpg_keyid
            target.telephone = telephone
            target.postal_address = postal_address
            target.comments = comments
            target.locale = locale
            target.timezone = timezone
        except TypeError:
            turbogears.flash(_('Your account details could not be saved: %s' % e))
        else:
            turbogears.flash(_('Your account details have been saved.'))
            turbogears.redirect("/user/view/%s" % target.username)
        return dict(target=target)

    # TODO: Decide who is allowed to see this.
    #@identity.require(turbogears.identity.in_group("accounts")) #TODO: Use auth.py
    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.user.list", allow_json=True)
    def list(self, search="a*"):
        '''List users
        '''
        re_search = re.sub(r'\*', r'%', search).lower()
        people = People.query.filter(People.username.like(re_search)).order_by('username')
        if people.count() < 0:
            turbogears.flash(_("No users found matching '%s'") % search)
        return dict(people=people, search=search)

    @expose(template='fas.templates.user.new')
    def new(self):
        if turbogears.identity.not_anonymous():
            turbogears.flash(_('No need to sign up, you have an account!'))
            turbogears.redirect('/user/view/%s' % turbogears.identity.current.user_name)
        return dict()

    @validate(validators=UserCreate())
    @error_handler(error)
    @expose(template='fas.templates.new')
    def create(self, username, human_name, email, telephone=None, postal_address=None):
        # TODO: Ensure that e-mails are unique?
        #       Also, perhaps implement a timeout- delete account
        #           if the e-mail is not verified (i.e. the person changes
        #           their password) withing X days.  
        import turbomail
        try:
            person = People()
            person.username = username
            person.human_name = human_name
            person.telephone = telephone
            person.password = '*'
            person.emails['primary'] = PersonEmails(email=email, purpose='primary')
            newpass = generate_password()
            message = turbomail.Message(config.get('accounts_mail'), person.emails['primary'].email, _('Welcome to the Fedora Project!'))
            message.plain = _('''
You have created a new Fedora account!
Your new password is: %s

Please go to https://admin.fedoraproject.org/fas/ to change it.

Welcome to the Fedora Project. Now that you've signed up for an
account you're probably desperate to start contributing, and with that
in mind we hope this e-mail might guide you in the right direction to
make this process as easy as possible.

Fedora is an exciting project with lots going on, and you can
contribute in a huge number of ways, using all sorts of different
skill sets. To find out about the different ways you can contribute to
Fedora, you can visit our join page which provides more information
about all the different roles we have available.

http://fedoraproject.org/en/join-fedora

If you already know how you want to contribute to Fedora, and have
found the group already working in the area you're interested in, then
there are a few more steps for you to get going.

Foremost amongst these is to sign up for the team or project's mailing
list that you're interested in - and if you're interested in more than
one group's work, feel free to sign up for as many mailing lists as
you like! This is because mailing lists are where the majority of work
gets organised and tasks assigned, so to stay in the loop be sure to
keep up with the messages.

Once this is done, it's probably wise to send a short introduction to
the list letting them know what experience you have and how you'd like
to help. From here, existing members of the team will help you to find
your feet as a Fedora contributor.

And finally, from all of us here at the Fedora Project, we're looking
forward to working with you!
''') % newpass['pass']
            turbomail.enqueue(message)
            person.password = newpass['hash']
            turbogears.flash(_('Your password has been emailed to you.  Please log in with it and change your password'))
            turbogears.redirect('/login')
        except KeyError:
            turbogears.flash(_("The username '%s' already Exists.  Please choose a different username.") % username)
            turbogears.redirect('/user/new')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.user.changepass")
    def changepass(self):
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=UserSetPassword())
    @error_handler(error)
    @expose(template="fas.templates.user.changepass")
    def setpass(self, currentpassword, password, passwordcheck):
        username = turbogears.identity.current.user_name
        person  = People.by_username(username)

#        current_encrypted = generate_password(currentpassword)
#        print "PASS: %s %s" % (current_encrypted, person.password)
        if not person.password == crypt.crypt(currentpassword, person.password):
            turbogears.flash('Your current password did not match')
            return dict()
        newpass = generate_password(password)
        try:
            person.password = newpass['hash']
            Log(author_id=person.id, description='Password changed')
            turbogears.flash(_("Your password has been changed."))
        except:
            Log(author_id=person.id, description='Password change failed!')
            turbogears.flash(_("Your password could not be changed."))
        return dict()

    @expose(template="fas.templates.user.resetpass")
    def resetpass(self):
        if turbogears.identity.not_anonymous():
            turbogears.flash(_('You are already logged in!'))
            turbogears.redirect('/user/view/%s' % turbogears.identity.current.user_name)
        return dict()

    @expose(template="fas.templates.user.resetpass")
    def sendpass(self, username, email, encrypted=False):
        import turbomail
        # Logged in
        if turbogears.identity.current.user_name:
            turbogears.flash(_("You are already logged in."))
            turbogears.redirect('/user/view/%s', turbogears.identity.current.user_name)
            return dict()
        person = People.by_username(username)
        if username and email:
            if not email == person.emails['primary'].email:
                turbogears.flash(_("username + email combo unknown."))
                return dict()
            newpass = generate_password()
            message = turbomail.Message(config.get('accounts_mail'), email, _('Fedora Project Password Reset'))
            mail = _('''
You have requested a password reset!
Your new password is: %s

Please go to https://admin.fedoraproject.org/fas/ to change it.
''') % newpass['pass']
            if encrypted:
                # TODO: Move this out to a single function (same as
                # CLA one), think of how to make sure this doesn't get
                # full of random keys (keep a clean Fedora keyring)
                # TODO: MIME stuff?
                keyid = re.sub('\s', '', person.gpg_keyid)
                ret = subprocess.call([config.get('gpgexec'), '--keyserver', config.get('gpg_keyserver'), '--recv-keys', keyid])
                if ret != 0:
                    turbogears.flash(_("Your key could not be retrieved from subkeys.pgp.net"))
                    turbogears.redirect('/cla/view/sign')
                    return dict()
                #try:
                #    subprocess.check_call([config.get('gpgexec'), '--keyserver', config.get('gpg_keyserver'), '--recv-keys', keyid])
                #except subprocess.CalledProcessError:
                #    turbogears.flash(_("Your key could not be retrieved from subkeys.pgp.net"))
                else:
                    try:
                        plaintext = StringIO.StringIO(mail)
                        ciphertext = StringIO.StringIO()
                        ctx = gpgme.Context()
                        ctx.armor = True
                        signer = ctx.get_key(re.sub('\s', '', config.get('gpg_fingerprint')))
                        ctx.signers = [signer]
                        recipient = ctx.get_key(keyid)
                        def passphrase_cb(uid_hint, passphrase_info, prev_was_bad, fd):
                            os.write(fd, '%s\n' % config.get('gpg_passphrase'))
                        ctx.passphrase_cb = passphrase_cb
                        ctx.encrypt_sign([recipient],
                            gpgme.ENCRYPT_ALWAYS_TRUST,
                            plaintext,
                            ciphertext)
                        message.plain = ciphertext.getvalue()
                    except:
                        turbogears.flash(_('Your password reset email could not be encrypted.  Your password has not been changed.'))
                        return dict()
            else:
                message.plain = mail;
            turbomail.enqueue(message)
            try:
                person.password = newpass['hash']
                turbogears.flash(_('Your new password has been emailed to you.'))
            except:
                turbogears.flash(_('Your password could not be reset.'))
            else:
                turbogears.redirect('/login')  
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="genshi-text:fas.templates.user.cert", format="text", content_type='text/plain; charset=utf-8')
    def gencert(self):
      from fas.openssl_fas import *
      username = turbogears.identity.current.user_name
      person = People.by_username(username)

      person.certificate_serial = person.certificate_serial + 1

      pkey = createKeyPair(TYPE_RSA, 1024);

      digest = config.get('openssl_digest')
      expire = config.get('openssl_expire')
      cafile = config.get('openssl_ca_file')

      cakey = retrieve_key_from_file(cafile)
      cacert = retrieve_cert_from_file(cafile)

      req = createCertRequest(pkey, digest=digest,
          C=config.get('openssl_c'),
          ST=config.get('openssl_st'),
          L=config.get('openssl_l'),
          O=config.get('openssl_o'),
          OU=config.get('openssl_ou'),
          CN=person.username,
          emailAddress=person.emails['primary'].email,
          )

      cert = createCertificate(req, (cacert, cakey), person.certificate_serial, (0, expire), digest='md5')
      certdump = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
      keydump = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
      return dict(cert=certdump, key=keydump)

    # Not sure where to take this yet.
    @identity.require(turbogears.identity.not_anonymous())
    @expose(format="json")
    def search(self, username=None, groupname=None):
        people = People.query.filter(People.username.like('%%%s%%' % username))
        return dict(people=people)

