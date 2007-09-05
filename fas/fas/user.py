import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler

import ldap

import fas.fasLDAP

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

from fas.auth import *

class knownUser(validators.FancyValidator):
    '''Make sure that a user already exists'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        p = Person.byUserName(value)
        if not p.cn:
            raise validators.Invalid(_("'%s' does not exist") % value, value, state)

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
            raise validators.Invalid(_("'%s' already exists") % value, value, state)

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
    cn = validators.All(unknownUser(not_empty=True, max=10), validators.String(max=32, min=3))
    givenName = validators.String(not_empty=True, max=42)
    mail = validators.All(
        validators.Email(not_empty=True, strip=True),
        nonFedoraEmail(not_empty=True, strip=True),
    )
    fedoraPersonBugzillaMail = validators.Email(not_empty=True, strip=True)
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

class User(controllers.Controller):

    def __init__(self):
        '''Create a User Controller.
        '''

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

    @validate(validators=userNameExists())
    @error_handler(error)
    @expose(template="fas.templates.user.view")
    @identity.require(turbogears.identity.not_anonymous())
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
        for g in groups:
            groupdata[g] = Groups.groups(g)[g]
        for g in groupsPending:
            groupdata[g] = Groups.groups(g)[g]
        try:
            groups['cla_done']
            claDone=True
        except KeyError:
            claDone=None
        return dict(user=user, groups=groups, groupsPending=groupsPending, groupdata=groupdata, claDone=claDone, personal=personal, admin=admin)

    @expose(template="fas.templates.user.edit")
    @identity.require(turbogears.identity.not_anonymous())
    def edit(self, userName=None):
        '''Edit a user
        '''
        if not userName:
            userName = turbogears.identity.current.user_name
        if not canEditUser(turbogears.identity.current.user_name, userName):
            turbogears.flash(_('You cannot edit %s') % userName )
            userName = turbogears.identity.current.user_name
        user = Person.byUserName(userName)
        value = {'userName': userName,
                 'givenName': user.givenName,
                 'mail': user.mail,
                 'fedoraPersonBugzillaMail': user.fedoraPersonBugzillaMail,
                 'fedoraPersonIrcNick': user.fedoraPersonIrcNick,
                 'fedoraPersonKeyId': user.fedoraPersonKeyId,
                 'telephoneNumber': user.telephoneNumber,
                 'postalAddress': user.postalAddress,
                 'description': user.description, }
        return dict(value=value)

    @validate(validators=editUser())
    @error_handler(error)
    @expose(template='fas.templates.editAccount')
    def save(self, userName, givenName, mail, fedoraPersonBugzillaMail, telephoneNumber, postalAddress, fedoraPersonIrcNick='', fedoraPersonKeyId='', description=''):
        if not canEditUser(turbogears.identity.current.user_name, userName):
            turbogears.flash(_("You do not have permission to edit '%s'", userName))
            turbogears.redirect('/user/edit/%s', turbogears.identity.current.user_name)
        user = Person.byUserName(userName)
        try:
            user.__setattr__('givenName', givenName.encode('utf8'))
            user.__setattr__('mail', mail.encode('utf8'))
            user.__setattr__('fedoraPersonBugzillaMail', fedoraPersonBugzillaMail.encode('utf8'))
            user.__setattr__('fedoraPersonIrcNick', fedoraPersonIrcNick.encode('utf8'))
            user.__setattr__('fedoraPersonKeyId', fedoraPersonKeyId.encode('utf8'))
            user.__setattr__('telephoneNumber', telephoneNumber.encode('utf8'))
            user.__setattr__('postalAddress', postalAddress.encode('utf8'))
            user.__setattr__('description', description.encode('utf8'))
        except:
            turbogears.flash(_('Your account details could not be saved.'))
            return dict()
        else:
            turbogears.flash(_('Your account details have been saved.'))
            turbogears.redirect("/user/view/%s" % userName)
            return dict()

    @expose(template="fas.templates.user.list")
    @identity.require(turbogears.identity.in_group("accounts"))
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
    def create(self, cn, givenName, mail, telephoneNumber, postalAddress):
        # TODO: Ensure that e-mails are unique?
        # Also, perhaps implement a timeout- delete account
        # if the e-mail is not verified (i.e. the person changes
        # their password) withing X days.  
        import turbomail
        try:
            Person.newPerson(cn.encode('utf8'),
                            givenName.encode('utf8'),
                            mail.encode('utf8'),
                            telephoneNumber.encode('utf8'),
                            postalAddress.encode('utf8'))
            p = Person.byUserName(cn.encode('utf8'))
            newpass = p.generatePassword()
            message = turbomail.Message('accounts@fedoraproject.org', p.mail, _('Fedora Project Password Reset'))
            message.plain = _("You have created a new Fedora account!  Your new password is: %s \nPlease go to https://admin.fedoraproject.org/fas/ to change it") % newpass['pass']
            turbomail.enqueue(message)
            p.__setattr__('userPassword', newpass['hash'])
            turbogears.flash(_('Your password has been emailed to you.  Please log in with it and change your password'))
            turbogears.redirect('/login')
        except ldap.ALREADY_EXISTS:
            turbogears.flash(_("The username '%s' already Exists.  Please choose a different username.") % cn)
            turbogears.redirect('/user/new')
        return dict()

    @expose(template="fas.templates.user.changepass")
    @identity.require(turbogears.identity.not_anonymous())
    def changepass(self):
        return dict()

    @validate(validators=changePass())
    @error_handler(error)
    @expose(template="fas.templates.user.changepass")
    @identity.require(turbogears.identity.not_anonymous())
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
            p.__setattr__('userPassword', newpass['hash'])
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
    def sendpass(self, userName, mail):
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
            message = turbomail.Message('accounts@fedoraproject.org', p.mail, _('Fedora Project Password Reset'))
            message.plain = _("You have requested a password reset!  Your new password is - %s \nPlease go to https://admin.fedoraproject.org/fas/ to change it") % newpass['pass']
            turbomail.enqueue(message)
            # TODO: Make this send GPG-encrypted e-mails :)
            try:
                p.__setattr__('userPassword', newpass['hash'])
                turbogears.flash(_('Your new password has been emailed to you.'))
                # This is causing an exception which causes the password could not be reset error.
#                turbogears.redirect('/login')  
            except:
                turbogears.flash(_('Your password could not be reset.'))
        return dict()

