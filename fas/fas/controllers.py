from turbogears import controllers, expose
# from model import *
from turbogears import identity, redirect, widgets, validate, validators, error_handler
from cherrypy import request, response
from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup
from turbogears import exception_handler
import turbogears
import ldap
# from fas import json
# import logging
# log = logging.getLogger("fas.controllers")


class knownUser(validators.FancyValidator):
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        p = Person.byUserName(value)
        if p.cn:
            raise validators.Invalid("'%s' already axists" % value, value, state)


class newPerson(widgets.WidgetsList):
#    cn = widgets.TextField(label='Username', validator=validators.PlainText(not_empty=True, max=10))
    cn = widgets.TextField(label='Username', validator=validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3)))
    givenName = widgets.TextField(label='Full Name', validator=validators.String(not_empty=True, max=42))
    mail = widgets.TextField(label='email', validator=validators.Email(not_empty=True, strip=True))
    telephoneNumber = widgets.TextField(label='Telephone Number', validator=validators.PhoneNumber(not_empty=True))
    postalAddress = widgets.TextArea(label='Postal Address', validator=validators.NotEmpty)

newPersonForm = widgets.TableForm(fields=newPerson(), submit_text='Sign Up')

class findUser(widgets.WidgetsList):
    userName = widgets.AutoCompleteField(label='Username', search_controller='search', search_param='userName', result_name='people')
    action = widgets.HiddenField(label='action', default='apply', validator=validators.String(not_empty=True))
    groupName = widgets.HiddenField(label='groupName', validator=validators.String(not_empty=True))

searchUserForm = widgets.TableForm(fields=findUser(), submit_text='Invite')


class Root(controllers.RootController):
    @expose(template="fas.templates.error")
    def errorMessage(self, tg_exceptions=None):
        ''' Generic exception handler'''
        # Maybe add a popup or alert or some damn thing.
        message = '%s' % tg_exceptions
        return dict(handling_value=True,exception=message)

    @expose(template="fas.templates.welcome")
    # @identity.require(identity.in_group("admin"))
    def index(self):
        import time
        # log.debug("Happy TurboGears Controller Responding For Duty")
        return dict(now=time.ctime())

    @expose(template="fas.templates.home")
    def home(self):
        from feeds import Koji
        builds = Koji(turbogears.identity.current.user_name)
        return dict(builds=builds)

    @expose(template="fas.templates.login")
    def login(self, forward_url=None, previous_url=None, *args, **kw):

        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            raise redirect(forward_url)

        forward_url=None
        previous_url= request.path

        if identity.was_login_attempted():
            msg=_("The credentials you supplied were not correct or "
                   "did not grant access to this resource.")
        elif identity.get_identity_errors():
            msg=_("You must provide your credentials before accessing "
                   "this resource.")
        else:
            msg=_("Please log in.")
            forward_url= request.headers.get("Referer", "/")

        response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=request.params,
                    forward_url=forward_url)

    @expose()
    def logout(self):
        identity.current.logout()
        raise redirect("/")

    @expose(template="fas.templates.editAccount")
    @identity.require(identity.not_anonymous())
    def editAccount(self,userName=None, action=None):
        if userName:
            try:
                Groups.byUserName(turbogears.identity.current.user_name)['accounts'].cn
                if not userName:
                    userName = turbogears.identity.current.user_name
            except KeyError:
                turbogears.flash('You cannot view %s' % userName )
                userName = turbogears.identity.current.user_name
        else:
                userName = turbogears.identity.current.user_name
        user = Person.byUserName(userName)
        groups = Groups.byUserName(userName)
        groupsPending = Groups.byUserName(userName, unapprovedOnly=True)
        try:
            groups['cla_done']
            claDone=True
        except KeyError:
            claDone=None
        return dict(user=user, groups=groups, groupsPending=groupsPending, action=action, claDone=claDone)

    @expose(template="fas.templates.editGroup")
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def editGroup(self, groupName):
        try:
            groups = Groups.byGroupName(groupName, includeUnapproved=True)
        except KeyError, e:
            raise ValueError, 'Group: %s - Does not exist!' % e
        group = Groups.groups(groupName)[groupName]
        userName = turbogears.identity.current.user_name
        try:
            myStatus = groups[userName].fedoraRoleStatus
        except KeyError:
            # Not in group
            myStatus = 'Not a Member'
        try:
            me = groups[userName]
        except:
            me = UserGroup()
        #searchUserForm.groupName.display('group')
        #findUser.groupName.display(value='fff')
        value = {'groupName' : group.cn}
        return dict(groups=groups, group=group, me=me, searchUserForm=searchUserForm, value=value)

    @expose(template="fas.templates.groupList")
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def listGroup(self, search='*'):
        groups = Groups.groups(search)
        userName = turbogears.identity.current.user_name
        myGroups = Groups.byUserName(userName)    
        try:
            groups.keys()
        except:
            turbogears.flash("No Groups found matching '%s'" % search)
            groups = {}
        return dict(groups=groups, search=search, myGroups=myGroups)


    @expose(template="fas.templates.resetPassword")
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    def resetPassword(self, userName=None, password=None, passwordCheck=None, mail=None):
        import turbomail

        # Logged in
        if turbogears.identity.current.user_name and not password:
            return dict()

        # Not logged in
        if not (userName and mail) and not turbogears.identity.current.user_name:
#            turbogears.flash('Please provide your username and password')
            return dict()

        if turbogears.identity.current.user_name:
            userName = turbogears.identity.current.user_name
        p = Person.byUserName(userName)

        if password and passwordCheck:
            if not password == passwordCheck:
                turbogears.flash('Passwords do not match!')
                return dict()
            if len(password) < 8:
                turbogears.flash('Password is too short.  Must be at least 8 characters long')
                return dict()
            newpass = p.generatePassword(password)

        if userName and mail and not turbogears.identity.current.user_name:
            if not mail == p.mail:
                turbogears.flash("username + email combo unknown.")
                return dict()
            newpass = p.generatePassword()
            message = turbomail.Message('accounts@fedoraproject.org', p.mail, 'Fedora Project Password Reset')
            message.plain = "You have requested a password reset!  Your new password is - %s \nPlease go to https://admin.fedoraproject.org/fas/ to change it" % newpass['pass']
            turbomail.enqueue(message)
            p.__setattr__('userPassword', newpass['hash'])

        p.userPassword = newpass['hash']
        print "PASS: %s" % newpass['pass']

        if turbogears.identity.current.user_name:
            turbogears.flash("Password Changed")
            turbogears.redirect("editAccount")
        else:
            turbogears.flash('Your password has been emailed to you')
            return dict()

    @expose(template="fas.templates.userList")
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
#    @identity.require(identity.in_group("accounts"))
    def listUser(self, search='a*'):
        users = Person.users(search)
        try:
            users[0]
        except:
            turbogears.flash("No users found matching '%s'" % search)
            users = []
        return dict(printList=users, search=search)

    listUsers = listUser

    @expose(template='fas.templates.edit')
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def editUserAttribute(self, attribute, value, userName=None):
        try:
            Groups.byUserName(turbogears.identity.current.user_name)['accounts'].cn
            if not userName:
                userName = turbogears.identity.current.user_name
        except KeyError:
            turbogears.flash('You cannot view %s' % userName )
            userName = turbogears.identity.current.user_name

        attribute = attribute.encode('utf8')
        value = value.encode('utf8')
        if attribute and value:
            p = Person.byUserName(userName)
            p.__setattr__(attribute, value)
            turbogears.flash("'%s' Updated to %s" % (attribute, value))
            if userName == turbogears.identity.current.user_name:
                turbogears.redirect('editAccount')
            else:
                turbogears.redirect('editAccount?userName=%s' % userName)
        return dict(userName=userName, attribute=attribute, value=value)

#    @expose(template='fas.templates.apply')
#    @exception_handler(errorMessage, rules="isinstance(tg_exceptions,ValueError)")
#    @identity.require(identity.not_anonymous())
#    def sudo(self, userName):
#        # This doesn't work
#        turbogears.identity.current.user_name=userName
#        turbogears.flash('Sudoed to %s' % userName)
#        turbogears.recirect('editAccount')

#    @error_handler(editGroup)
#    @validate(form=newPersonForm)
    @expose(template='fas.templates.apply')
    @identity.require(identity.not_anonymous())
    def modifyGroup(self, groupName, action, userName, **kw):
        ''' Modifies group based on action, groupName and userName '''
        try:
            userName = userName['text']
        except TypeError:
            pass

        sponsor = turbogears.identity.current.user_name
        try:
            group = Groups.groups(groupName)[groupName]
        except KeyError, e:
            turbogears.flash('Group Error: %s does not exist - %s' % (groupName, e))
            turbogears.redirect('editGroup?groupName=%s' % group.cn)
        try:
            p = Person.byUserName(userName)
            if not p.cn:
                raise KeyError, 'User %s, just not there' % userName
        except KeyError, e:
            turbogears.flash('User Error: %s does not exist - %s' % (userName, e))
            turbogears.redirect('editGroup?groupName=%s' % group.cn)

        g = Groups.byGroupName(groupName, includeUnapproved=True)

        # Apply user to a group (as in application)
        if action == 'apply':
            try:
                Groups.apply(groupName, userName)
            except ldap.ALREADY_EXISTS:
                turbogears.flash('%s Already in group!' % p.cn)
                turbogears.redirect('editGroup?groupName=%s' % group.cn)
            else:
                turbogears.flash('%s Applied!' % p.cn)
                turbogears.redirect('editGroup?groupName=%s' % group.cn)

        # Some error checking for the sponsors
        if g[userName].fedoraRoleType.lower() == 'administrator' and g[sponsor].fedoraRoleType.lower() == 'sponsor':
            raise ValueError, 'Sponsors cannot alter administrators.  End of story'

        try:
            userGroup = Groups.byGroupName(groupName)[userName]
        except KeyError:
            # User not already in the group (happens when users apply for a group)
            userGroup = UserGroup()
            pass

        # Remove user from a group
        if action == 'remove':
            try:
                Groups.remove(group.cn, p.cn)
            except TypeError:
                turbogears.flash('%s could not be removed from %s!' % (p.cn, group.cn))
                turbogears.redirect('editGroup?groupName=%s' % group.cn)
            else:
                turbogears.flash('%s removed from %s!' % (p.cn, group.cn))
                turbogears.redirect('editGroup?groupName=%s' % group.cn)
            return dict()

        # Upgrade user in a group
        elif action == 'upgrade':
            if g[userName].fedoraRoleType.lower() == 'sponsor' and g[sponsor].fedoraRoleType.lower() == 'sponsor':
                raise ValueError, 'Sponsors cannot admin other sponsors'
            try:
                p.upgrade(groupName)
            except TypeError, e:
                turbogears.flash('Cannot upgrade %s - %s!' % (p.cn, e))
                turbogears.redirect('editGroup?groupName=%s' % group.cn)
            turbogears.flash('%s Upgraded!' % p.cn)
            turbogears.redirect('editGroup?groupName=%s' % group.cn)


        # Downgrade user in a group
        elif action == 'downgrade':
            if g[userName].fedoraRoleType.lower() == 'administrator' and g[sponsor].fedoraRoleType.lower() == 'sponsor':
                raise ValueError, 'Sponsors cannot downgrade admins'
            try:
                p.downgrade(groupName)
            except TypeError, e:
                turbogears.flash('Cannot downgrade %s - %s!' % (p.cn, e))
                turbogears.redirect('editGroup?groupName=%s' % group.cn)
            turbogears.flash('%s Downgraded!' % p.cn)
            turbogears.redirect('editGroup?groupName=%s' % group.cn)

        # Sponsor / Approve User
        elif action == 'sponsor' or action == 'apply':
            p.sponsor(groupName, sponsor)
            turbogears.flash('%s has been sponsored!' % p.cn)
            turbogears.redirect('editGroup?groupName=%s' % group.cn)

        turbogears.flash('Invalid action: %s' % action)
        turbogears.redirect('editGroup?groupName=%s' % group.cn)
        return dict()

    @expose(template='fas.templates.inviteMember')
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def inviteMember(self, name=None, email=None, skills=None):
        if name and email:
            turbogears.flash('Invitation Sent to: "%s" <%s>' % (name, email))
        if name or email:
            turbogears.flash('Please provide both an email address and the persons name.')
        return dict()

    @expose(template='fas.templates.apply')
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def applyForGroup(self, groupName, action=None, requestField=None):
        userName = turbogears.identity.current.user_name

        group = Groups.groups(groupName)[groupName]
        user = Person.byUserName(userName)
        if action != 'Remove':
            try:
                Groups.apply(groupName, userName)
                turbogears.flash('Application sent for %s' % user.cn)
            except ldap.ALREADY_EXISTS, e:
                turbogears.flash('Application Denied: %s' % e[0]['desc'])
            turbogears.redirect('editGroup?groupName=%s' % group.cn)

        if action == 'Remove' and group.fedoraGroupUserCanRemove == 'TRUE':
            try:
                Groups.remove(group.cn, user.cn)
            except TypeError:
                turbogears.flash('%s could not be removed from %s!' % (user.cn, group.cn))
                turbogears.redirect('editGroup?groupName=%s' % group.cn)
            else:
                turbogears.flash('%s removed from %s!' % (user.cn, group.cn))
                turbogears.redirect('editGroup?groupName=%s' % group.cn)
        else:
            turbogears.flash('%s does not allow self removal' % group.cn)
            turbogears.redirect('editGroup?groupName=%s' % group.cn)
        return dict()

    @expose(template='fas.templates.signUp')
    def signUp(self):
        if turbogears.identity.not_anonymous():
            turbogears.flash('No need to sign up, You have an account!')
            turbogears.redirect('editAccount')
        return dict(form=newPersonForm)

    @validate(form=newPersonForm)
    @error_handler(signUp)
    @expose(template='fas.templates.signUp')
    def newAccountSubmit(self, cn, givenName, mail, telephoneNumber, postalAddress):
        import turbomail
        try:
            Person.newPerson(cn.encode('utf8'), givenName.encode('utf8'), mail.encode('utf8'), telephoneNumber.encode('utf8'), postalAddress.encode('utf8'))
            p = Person.byUserName(cn.encode('utf8'))
            newpass = p.generatePassword()
            message = turbomail.Message('accounts@fedoraproject.org', p.mail, 'Fedora Project Password Reset')
            message.plain = "You have requested a password reset!  Your new password is - %s \nPlease go to https://admin.fedoraproject.org/fas/ to change it" % newpass['pass']
            turbomail.enqueue(message)
            p.__setattr__('userPassword', newpass['hash'])
            turbogears.flash('Your password has been emailed to you.  Please log in with it and change your password')
            turbogears.redirect('/')

        except ldap.ALREADY_EXISTS:
            turbogears.flash('%s Already Exists, Please pick a different name' % cn)
            turbogears.redirect('signUp')
        return dict()

    @expose(format="json")
    def search(self, userName=None, groupName=None):
        people = Person.users('%s*' % userName)
        return dict(people=
                filter(lambda item: userName in item.lower(), people))

    @expose(format="json")
    def help(self, helpID='Unknown'):
        messages = { 
            'Unknown' : ''' Unknown:  If you know what help should be here, please email accounts@fedoraproject.org and tell them.''',
            'postalAddress' : ''' Postal Address: Your local mailing address.  It could be a work address or a home address.''',
            'cn' : ''' Account Name: A unique identifier for each user.  This is your 'username' for many parts of fedora.  This will also be your @fedoraproject.org email alias.''',
            'givenName' : ''' Real Name: This is your full name, often Firstname Lastname.''',
            'mail' : ''' Email Address: This is your primary email address.  Notifications, aliases, password resets all get sent to this address.  Other email addresses can be added (like bugzilla address)''',
            'fedoraPersonBugzillaMail' : ''' Bugzilla Email:  For most this is the same address as as their primary email address.''',
            'fedoraPersonIrcNick' : ''' IRC Nick: Many fedora developers can be found on freenode.net.  Make sure your nick is registered so no one else takes it.  After you have registered, let the rest of fedora know what your nick is.''',
            'fedoraPersonKeyId' : ''' PGP Key: PGP key's are required to verify your identity to others and to encrypt messages.  It is required in order to sign the CLA and, as such, is required to be a contributor.  In order to create and upload your key please see our howto at: <a href='http://fedoraproject.org/wiki/DocsProject/UsingGpg/CreatingKeys'>http://fedoraproject.org/wiki/DocsProject/UsingGpg/CreatingKeys</a> ''',
            'telephoneNumber' : ''' Telephone Number: Please include a country code if outside of the united states. ''',
            'description' : ''' Description: Just a brief comment on yourself.  Could include your website or blog. ''',
            'password' : ''' Password: Used to access fedora resources.  Resources that don't require your password may require ssh keys ''',
            'accountStatus' : ''' Account Status: Some accounts may be disabled because of misconduct or password expiration.  If your account is not active and you are not sure why, please contact <a href='mailto:accounts@fedoraproject.org>accounts@fedoraproject.org</a> or join #fedora-admin on <a href='http://irc.freenode.net/'>irc.freenode.net</a> ''',
            'cla' : ''' Contributor License Agreement: This agreement is required in order to be a Fedora contributor.  The CLA can be found at: <a href='http://fedoraproject.org/wiki/Legal/Licenses/CLA'>http://fedoraproject.org/wiki/Legal/Licenses/CLA</a> ''',
            'inviteToGroup' : ''' This will add a user to the following group.  They will initially be unapproved, just as if they had applied themselves.  An email notification will be sent. '''
            }
        try:
            messages[helpID]
        except KeyError:
            helpID='Unknown'
        return dict(help=messages[helpID])
                #filter(lambda item: userName in item.lower(), people))



    @expose(template='fas.templates.invite')
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def invite(self, target=None):
        import turbomail
        user = Person.byUserName(turbogears.identity.current.user_name)
        if target:
            message = turbomail.Message(user.mail, target, 'Come join The Fedora Project!')
#            message.plain = "Please come join the fedora project!  Someone thinks your skills and abilities may be able to help our project.  If your interested please go to http://fedoraproject.org/wiki/HelpWanted"
            message.plain = "%s <%s> has invited you to join the Fedora \
Project!  We are a community of users and developers who produce a \
complete operating system from entirely free and open source software \
(FOSS).  %s thinks that you have knowledge and skills \
that make you a great fit for the Fedora community, and that you might \
be interested in contributing. \n\
\n\
How could you team up with the Fedora community to use and develop your \
skills?  Check out http://fedoraproject.org/wiki/Join for some ideas. \
Our community is more than just software developers -- we also have a \
place for you whether you're an artist, a web site builder, a writer, or \
a people person.  You'll grow and learn as you work on a team with other \
very smart and talented people. \n\
\n\
Fedora and FOSS are changing the world -- come be a part of it!" % (user.givenName, user.mail, user.givenName)
            turbomail.enqueue(message)
            turbogears.flash('Message sent to: %s' % target)
        return dict(target=target, user=user)

def relativeUser(realUser, sudoUser):
    ''' Takes user and sees if they are allow to sudo for remote group'''
    p = Person.byUserName('realUser')


