import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler

import ldap

import os
import re
import gpgme
import StringIO

import fas.fasLDAP

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

from fas.model import People

from fas.auth import *

from textwrap import dedent

class knownUser(validators.FancyValidator):
    '''Make sure that a user already exists'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        try:
            p = People.by_username(value)
        except InvalidRequestError:
            raise validators.Invalid(_("'%s' does not exist.") % value, value, state)

class nonFedoraEmail(validators.FancyValidator):
    '''Make sure that an email address is not @fedoraproject.org'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        p = Person.byUserName(value)
        if value.endswith('@fedoraproject.org'):
            raise validators.Invalid(_("To prevent email loops, your email address cannot be @fedoraproject.org."), value, state)

class unknownUser(validators.FancyValidator):
    '''Make sure that a user doesn't already exist'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        p = Person.byUserName(value)
        if p.cn:
            raise validators.Invalid(_("'%s' already exists.") % value, value, state)

class userNameAllowed(validators.FancyValidator):
    '''Make sure that a username isn't blacklisted'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        username_blacklist = config.get('username_blacklist')
        if re.compile(username_blacklist).match(value):
          raise validators.Invalid(_("'%s' is an illegal username.") % value, value, state)

class editUser(validators.Schema):
    userName = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))
    givenName = validators.String(not_empty=True, max=42)
    mail = validators.All(
        validators.Email(not_empty=True, strip=True),
        nonFedoraEmail(not_empty=True, strip=True),
    )
    fedoraPersonBugzillaMail = validators.Email(not_empty=True, strip=True)
    #fedoraPersonKeyId- Save this one for later :)
    telephoneNumber = validators.PhoneNumber(not_empty=True)
    postalAddress = validators.NotEmpty
    
class newUser(validators.Schema):
    cn = validators.All(
        unknownUser(not_empty=True, max=10),
        userNameAllowed(not_empty=True),
        validators.String(max=32, min=3),
    )
    givenName = validators.String(not_empty=True, max=42)
    mail = validators.All(
        validators.Email(not_empty=True, strip=True),
        nonFedoraEmail(not_empty=True, strip=True),
    )
    fedoraPersonBugzillaMail = validators.Email(strip=True)
    telephoneNumber = validators.PhoneNumber(not_empty=True)
    postalAddress = validators.NotEmpty

class changePass(validators.Schema):
    currentPassword = validators.String()
    # TODO (after we're done with most testing): Add complexity requirements?
    password = validators.String(min=8)
    passwordCheck = validators.String()
    chained_validators = [validators.FieldsMatch('password', 'passwordCheck')]

class userNameExists(validators.Schema):
    userName = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))


class userNameExists(validators.Schema):
    userName = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))

class User(controllers.Controller):

    def __init__(self):
        '''Create a User Controller.
        '''

    @identity.require(turbogears.identity.not_anonymous())
    def index(self):
        '''Redirect to view
        '''
        turbogears.redirect('view/%s' % turbogears.identity.current.user_name)

    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=userNameExists())
    @error_handler(error)
    @expose(template="fas.templates.user.view")
    def view(self, userName=None):
        '''View a User.
        '''
        if not userName:
            userName = turbogears.identity.current.user_name
        if turbogears.identity.current.user_name == userName:
            personal = True
        else:
            personal = False
        if isAdmin(turbogears.identity.current.user_name):
            admin = True
        else:
            admin = False
        user = Person.byUserName(userName)
        groups = Groups.byUserName(userName)
        groupsPending = Groups.byUserName(userName, unapprovedOnly=True)
        groupdata={}
        groupUnapproved={}
        for g in groups:
            groupdata[g] = Groups.groups(g)[g]
            unapproved = Groups.byGroupName(g, unapprovedOnly=True)
            unapproved = [(v,k) for k,v in unapproved.items()]
            unapproved.sort(date_compare)
            unapproved.reverse()
            groupUnapproved[g] = [(Person.byUserName(k).givenName,v) for v,k in unapproved]
        for g in groupsPending:
            groupdata[g] = Groups.groups(g)[g]
        try:
            groups['cla_done']
            claDone=True
        except KeyError:
            claDone=None
        return dict(user=user, groups=groups, groupsPending=groupsPending, groupdata=groupdata, groupUnapproved=groupUnapproved, claDone=claDone, personal=personal, admin=admin)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=userNameExists())
    @error_handler(error)
    @expose(template="fas.templates.user.edit")
    def edit(self, userName=None):
        '''Edit a user
        '''
        print "User: %s" % userName
        if not userName:
            userName = turbogears.identity.current.username
        if not canEditUser(turbogears.identity.current.user_name, userName):
            turbogears.flash(_('You cannot edit %s') % userName )
            userName = turbogears.identity.current.username
        user = People.by_username(userName)
        
        return dict(userName=userName, user=user)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=editUser())
    @error_handler(error)
    @expose(template='fas.templates.user.edit')
    def save(self, userName, givenName, mail, fedoraPersonBugzillaMail, telephoneNumber, postalAddress, fedoraPersonIrcNick='', fedoraPersonKeyId='', description='', fedoraPersonTimeZone='UTC'):
        if not canEditUser(turbogears.identity.current.user_name, userName):
            turbogears.flash(_("You do not have permission to edit '%s'" % userName))
            turbogears.redirect('/user/edit/%s', turbogears.identity.current.user_name)
            return dict()
        user = Person.byUserName(userName)
        try:
            user.givenName = givenName
            user.mail = mail
            user.fedoraPersonBugzillaMail = fedoraPersonBugzillaMail
            user.fedoraPersonIrcNick = fedoraPersonIrcNick
            user.fedoraPersonKeyId = fedoraPersonKeyId
            user.telephoneNumber = telephoneNumber
            user.postalAddress = postalAddress
            user.description = description
            user.fedoraPersonTimeZone = fedoraPersonTimeZone
        except:
            turbogears.flash(_('Your account details could not be saved.'))
        else:
            turbogears.flash(_('Your account details have been saved.'))
            turbogears.redirect("/user/view/%s" % userName)
        return dict(userName=userName, user=user)

    @identity.require(turbogears.identity.in_group("accounts")) #TODO: Use auth.py
    @expose(template="fas.templates.user.list")
    def list(self, search="a*"):
        '''List users
        '''
        users = Person.users(search)
        try:
            users[0]
        except:
            turbogears.flash(_("No users found matching '%s'") % search)
            users = []
        cla_done = Groups.byGroupName('cla_done')
        claDone = {}
        for u in users:
            try:
                cla_done[u]
                claDone[u] = True
            except KeyError:
                claDone[u] = False
        return dict(users=users, claDone=claDone, search=search)
       
    @expose(template='fas.templates.user.new')
    def new(self):
        if turbogears.identity.not_anonymous():
            turbogears.flash(_('No need to sign up, You have an account!'))
            turbogears.redirect('/user/view/%s' % turbogears.identity.current.user_name)
        return dict()

    @validate(validators=newUser())
    @error_handler(error)
    @expose(template='fas.templates.new')
    def create(self, cn, givenName, mail, telephoneNumber, postalAddress, fedoraPersonBugzillaMail=''):
        # TODO: Ensure that e-mails are unique- this should probably be done in the LDAP schema.
        #       Also, perhaps implement a timeout- delete account
        #           if the e-mail is not verified (i.e. the person changes
        #           their password) withing X days.  
        import turbomail
        try:
            Person.newPerson(cn,
                             givenName,
                             mail,
                             telephoneNumber,
                             postalAddress,)
            p = Person.byUserName(cn)
            newpass = p.generatePassword()
            message = turbomail.Message(config.get('accounts_mail'), p.mail, _('Fedora Project Password Reset'))
            message.plain = _(dedent('''
                 You have created a new Fedora account!
                 Your new password is: %s

                 Please go to https://admin.fedoraproject.org/fas/ to change it.
                 ''') % newpass['pass'])
            turbomail.enqueue(message)
            p.userPassword = newpass['hash']
            turbogears.flash(_('Your password has been emailed to you.  Please log in with it and change your password'))
            turbogears.redirect('/login')
        except ldap.ALREADY_EXISTS:
            turbogears.flash(_("The username '%s' already Exists.  Please choose a different username.") % cn)
            turbogears.redirect('/user/new')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.user.changepass")
    def changepass(self):
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=changePass())
    @error_handler(error)
    @expose(template="fas.templates.user.changepass")
    def setpass(self, currentPassword, password, passwordCheck):
        userName = turbogears.identity.current.user_name
        try:
            Person.auth(userName, currentPassword)
        except AuthError:
            turbogears.flash('Your current password did not match.')
            return dict()
        p = Person.byUserName(userName)
        newpass = p.generatePassword(password)
        try:
            p.userPassword = newpass['hash']
            turbogears.flash(_("Your password has been changed."))
        except:
            turbogears.flash(_("Your password could not be changed."))
        return dict()

    @expose(template="fas.templates.user.resetpass")
    def resetpass(self):
        if turbogears.identity.not_anonymous():
            turbogears.flash(_('You are already logged in!'))
            turbogears.redirect('/user/view/%s' % turbogears.identity.current.user_name)
        return dict()
            
    @expose(template="fas.templates.user.resetpass")
    def sendpass(self, userName, mail, encrypted=False):
        import turbomail
        # Logged in
        if turbogears.identity.current.user_name:
            turbogears.flash(_("You are already logged in."))
            turbogears.redirect('/user/view/%s', turbogears.identity.current.user_name)
            return dict()
        p = Person.byUserName(userName)
        if userName and mail:
            if not mail == p.mail:
                turbogears.flash(_("username + email combo unknown."))
                return dict()
            newpass = p.generatePassword()
            message = turbomail.Message(config.get('accounts_mail'), p.mail, _('Fedora Project Password Reset'))
            email = _(dedent('''
                You have requested a password reset!
                Your new password is - %s
                
                Please go to https://admin.fedoraproject.org/fas/ to change it.
                ''')) % newpass['pass']
            if encrypted:
                try:
                    plaintext = StringIO.StringIO(email)
                    ciphertext = StringIO.StringIO()
                    ctx = gpgme.Context()
                    ctx.armor = True
                    signer = ctx.get_key(re.sub('\s', '', config.get('gpg_fingerprint')))
                    ctx.signers = [signer]
                    recipient = ctx.get_key(re.sub('\s', '', p.fedoraPersonKeyId))
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
                message.plain = email;
            turbomail.enqueue(message)
            try:
                p.userPassword = newpass['hash']
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
      user = Person.byUserName(turbogears.identity.current.user_name)
      user.fedoraPersonCertSerial = int(user.fedoraPersonCertSerial) + 1

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
          CN=user.cn,
          emailAddress=user.mail,
          )

      cert = createCertificate(req, (cacert, cakey), int(user.fedoraPersonCertSerial), (0, expire), digest='md5')
      certdump = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
      keydump = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
      return dict(cert=certdump, key=keydump)

    @expose(format="json")
    def search(self, userName=None, groupName=None):
        people = Person.users('%s*' % userName)
        return dict(people=
                filter(lambda item: userName in item.lower(), people))

def date_compare(x, y):
    if x[0].fedoraRoleCreationDate > y[0].fedoraRoleCreationDate:
        return 1
    elif x[0].fedoraRoleCreationDate == y[0].fedoraRoleCreationDate:
        return 0
    else:
        return -1

