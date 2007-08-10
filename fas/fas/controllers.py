from turbogears import controllers, expose, config
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
import time
# from fas import json
# import logging
# log = logging.getLogger("fas.controllers")

ADMINGROUP = config.get('admingroup')

class knownUser(validators.FancyValidator):
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        p = Person.byUserName(value)
        if p.cn:
            raise validators.Invalid(_("'%s' already exists") % value, value, state)

class unknownUser(validators.FancyValidator):
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        p = Person.byUserName(value)
        if not p.cn:
            raise validators.Invalid(_("'%s' does not exist") % value, value, state)

class unknownGroup(validators.FancyValidator):
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        g = Groups.groups(groupName)
        if not g:
            raise validators.Invalid(_("'%s' does not exist") % value, value, state)


class newPerson(widgets.WidgetsList):
#    cn = widgets.TextField(label='Username', validator=validators.PlainText(not_empty=True, max=10))
    cn = widgets.TextField(label=_('Username'), validator=validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3)))
    givenName = widgets.TextField(label=_('Full Name'), validator=validators.String(not_empty=True, max=42))
    mail = widgets.TextField(label=_('email'), validator=validators.Email(not_empty=True, strip=True))
    telephoneNumber = widgets.TextField(label=_('Telephone Number'), validator=validators.PhoneNumber(not_empty=True))
    postalAddress = widgets.TextArea(label=_('Postal Address'), validator=validators.NotEmpty)

newPersonForm = widgets.ListForm(fields=newPerson(), submit_text=_('Sign Up'))

class editPerson(widgets.WidgetsList):
#    cn = widgets.TextField(label='Username', validator=validators.PlainText(not_empty=True, max=10))
    userName = widgets.HiddenField(validator=validators.All(unknownUser(not_empty=True, max=10), validators.String(max=32, min=3)))
    givenName = widgets.TextField(label=_('Full Name'), validator=validators.String(not_empty=True, max=42))
    mail = widgets.TextField(label=_('Email'), validator=validators.Email(not_empty=True, strip=True))
    fedoraPersonBugzillaMail = widgets.TextField(label=_('Bugzilla Email'), validator=validators.Email(not_empty=True, strip=True))
    fedoraPersonIrcNick = widgets.TextField(label=_('IRC Nick'))
    fedoraPersonKeyId = widgets.TextField(label=_('PGP Key'))
    telephoneNumber = widgets.TextField(label=_('Telephone Number'), validator=validators.PhoneNumber(not_empty=True))
    postalAddress = widgets.TextArea(label=_('Postal Address'), validator=validators.NotEmpty)
    description = widgets.TextArea(label=_('Description'))

editPersonForm = widgets.ListForm(fields=editPerson(), submit_text=_('Update'))

class editGroup(widgets.WidgetsList):
    groupName = widgets.HiddenField(validator=validators.All(unknownGroup(not_empty=True, max=10), validators.String(max=32, min=3)))
    fedoraGroupDesc = widgets.TextField(label=_('Description'), validator=validators.NotEmpty)
    fedoraGroupOwner = widgets.TextField(label=_('Group Owner'), validator=validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3)))
    fedoraGroupNeedsSponsor = widgets.CheckBox(label=_('Needs Sponsor'))
    fedoraGroupUserCanRemove = widgets.CheckBox(label=_('Self Removal'))
    fedoraGroupJoinMsg = widgets.TextField(label=_('Group Join Message'))

editGroupForm = widgets.ListForm(fields=editGroup(), submit_text=_('Update'))

class findUser(widgets.WidgetsList):
    userName = widgets.AutoCompleteField(label=_('Username'), search_controller='search', search_param='userName', result_name='people')
    action = widgets.HiddenField(default='apply', validator=validators.String(not_empty=True))
    groupName = widgets.HiddenField(validator=validators.String(not_empty=True))

searchUserForm = widgets.ListForm(fields=findUser(), submit_text=_('Invite'))


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
        # log.debug("Happy TurboGears Controller Responding For Duty")
        if turbogears.identity.not_anonymous():
            turbogears.redirect('home')
        return dict(now=time.ctime())

    @expose(template="fas.templates.home")
    def home(self):
        from feeds import Koji
        builds = Koji(turbogears.identity.current.user_name)
        return dict(builds=builds)

    @expose(template="fas.templates.dump", format="plain", content_type="text/plain")
    def groupDump(self, groupName=None):
        groups = Groups.byGroupName(groupName)
        return dict(groups=groups, Person=Person)

    @expose(template="fas.templates.login")
    def login(self, forward_url=None, previous_url=None, *args, **kw):

        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            turbogears.flash(_('Welcome, %s') % Person.byUserName(turbogears.identity.current.user_name).givenName)
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
        turbogears.flash(_('You have successfully logged out.'))
        raise redirect("/")

    @expose(template="fas.templates.viewAccount")
    @identity.require(identity.not_anonymous())
    def viewAccount(self,userName=None, action=None):
        if not userName:
            userName = turbogears.identity.current.user_name
        if turbogears.identity.current.user_name == userName:
            personal = True
        else:
            personal = False
        try:
            Groups.byUserName(turbogears.identity.current.user_name)[ADMINGROUP].cn
            admin = True
        except KeyError:
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
        return dict(user=user, groups=groups, groupsPending=groupsPending, action=action, groupdata=groupdata, claDone=claDone, personal=personal, admin=admin)

    @expose(template="fas.templates.editAccount")
    @identity.require(identity.not_anonymous())
    def editAccount(self, userName=None, action=None):
        if userName:
            try:
                Groups.byUserName(turbogears.identity.current.user_name)[ADMINGROUP].cn
                if not userName:
                    userName = turbogears.identity.current.user_name
            except KeyError:
                turbogears.flash(_('You cannot edit %s') % userName )
                userName = turbogears.identity.current.user_name
        else:
                userName = turbogears.identity.current.user_name
        user = Person.byUserName(userName)
        value = {'userName' : userName,
                  'givenName' : user.givenName,
                  'mail' : user.mail,
                  'fedoraPersonBugzillaMail' : user.fedoraPersonBugzillaMail,
                  'fedoraPersonIrcNick' : user.fedoraPersonIrcNick,
                  'fedoraPersonKeyId' : user.fedoraPersonKeyId,
                  'telephoneNumber' : user.telephoneNumber,
                  'postalAddress' : user.postalAddress,
                  'description' : user.description, }
        return dict(form=editPersonForm, value=value)

    @expose(template="fas.templates.viewGroup")
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def viewGroup(self, groupName):
        try:
            groups = Groups.byGroupName(groupName, includeUnapproved=True)
        except KeyError:
            raise ValueError, _('Group: %s - Does not exist!') % groupName
        try:
            group = Groups.groups(groupName)[groupName]
        except TypeError:
            raise ValueError, _('Group: %s - Does not exist!') % groupName
        userName = turbogears.identity.current.user_name
        try:
            myStatus = groups[userName].fedoraRoleStatus
        except KeyError:
            # Not in group
            myStatus = 'Not a Member' # This has say 'Not a Member'
        except TypeError:
            groups = {}
        try:
            me = groups[userName]
        except:
            me = UserGroup()
        #searchUserForm.groupName.display('group')
        #findUser.groupName.display(value='fff')
        value = {'groupName' : group.cn}
        return dict(groups=groups, group=group, me=me, searchUserForm=searchUserForm, value=value)

    @expose(template="fas.templates.editGroup")
    @identity.require(identity.not_anonymous())
    def editGroup(self, groupName, action=None):
        userName = turbogears.identity.current.user_name
        try:
            Groups.byUserName(userName)[ADMINGROUP].cn
        except KeyError:
            try:
                Groups.byUserName(userName)[groupName]
                if Groups.byUserName(userName)[groupName].fedoraRoleType.lower() != 'administrator':
                    raise KeyError
            except KeyError:
                turbogears.flash(_('You cannot edit %s') % groupName)
                turbogears.redirect('viewGroup?groupName=%s' % groupName)
        group = Groups.groups(groupName)[groupName]
        value = {'groupName' : groupName,
                  'fedoraGroupOwner' : group.fedoraGroupOwner,
                  'fedoraGroupType' : group.fedoraGroupType,
                  'fedoraGroupNeedsSponsor' : (group.fedoraGroupNeedsSponsor.upper() == 'TRUE'),
                  'fedoraGroupUserCanRemove' : (group.fedoraGroupUserCanRemove.upper() == 'TRUE'),
                  'fedoraGroupJoinMsg' : group.fedoraGroupJoinMsg,
                  'fedoraGroupDesc' : group.fedoraGroupDesc, }
                  #'fedoraGroupRequires' : group.fedoraGroupRequires, }
        return dict(form=editGroupForm, value=value)

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
            turbogears.flash(_("No Groups found matching '%s'") % search)
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
                turbogears.flash(_('Passwords do not match!'))
                return dict()
            if len(password) < 8:
                turbogears.flash(_('Password is too short.  Must be at least 8 characters long'))
                return dict()
            newpass = p.generatePassword(password)

        if userName and mail and not turbogears.identity.current.user_name:
            if not mail == p.mail:
                turbogears.flash(_("username + email combo unknown."))
                return dict()
            newpass = p.generatePassword()
            message = turbomail.Message('accounts@fedoraproject.org', p.mail, _('Fedora Project Password Reset'))
            message.plain = _("You have requested a password reset!  Your new password is - %s \nPlease go to https://admin.fedoraproject.org/fas/ to change it") % newpass['pass']
            turbomail.enqueue(message)
            p.__setattr__('userPassword', newpass['hash'])

        p.userPassword = newpass['hash']
        print "PASS: %s" % newpass['pass']

        if turbogears.identity.current.user_name:
            turbogears.flash(_("Password Changed"))
            turbogears.redirect("viewAccount")
        else:
            turbogears.flash(_('Your password has been emailed to you'))
            return dict()

    @expose(template="fas.templates.userList")
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.in_group("accounts"))
    def listUser(self, search='a*'):
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

    listUsers = listUser

#    @expose(template='fas.templates.apply')
#    @exception_handler(errorMessage, rules="isinstance(tg_exceptions,ValueError)")
#    @identity.require(identity.not_anonymous())
#    def sudo(self, userName):
#        # This doesn't work
#        turbogears.identity.current.user_name=userName
#        turbogears.flash('Sudoed to %s' % userName)
#        turbogears.recirect('viewAccount')

#    @error_handler(viewGroup)
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
        except KeyError:
            turbogears.flash(_('Group Error: %s does not exist.') % groupName)
            turbogears.redirect('viewGroup?groupName=%s' % group.cn)
        try:
            p = Person.byUserName(userName)
            if not p.cn:
                raise KeyError, userName
        except KeyError:
            turbogears.flash(_('User Error: User %s does not exist.') % userName)
            turbogears.redirect('viewGroup?groupName=%s' % group.cn)

        g = Groups.byGroupName(groupName, includeUnapproved=True)

        # Apply user to a group (as in application)
        if action == 'apply':
            try:
                Groups.apply(groupName, userName)
            except ldap.ALREADY_EXISTS:
                turbogears.flash(_('%s Already in group!') % p.cn)
                turbogears.redirect('viewGroup?groupName=%s' % group.cn)
            else:
                turbogears.flash(_('%s Applied!') % p.cn)
                turbogears.redirect('viewGroup?groupName=%s' % group.cn)

        # Some error checking for the sponsors
        if g[userName].fedoraRoleType.lower() == 'administrator' and g[sponsor].fedoraRoleType.lower() == 'sponsor':
            raise ValueError, _('Sponsors cannot alter administrators.  End of story.')

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
                turbogears.flash(_('%(name)s could not be removed from %(group)s!') % {'name' : p.cn, 'group' : group.cn})
                turbogears.redirect('viewGroup?groupName=%s' % group.cn)
            else:
                turbogears.flash(_('%(name)s removed from %(group)s!') % {'name' : p.cn, 'group' : group.cn})
                turbogears.redirect('viewGroup?groupName=%s' % group.cn)
            return dict()

        # Upgrade user in a group
        elif action == 'upgrade':
            if g[userName].fedoraRoleType.lower() == 'sponsor' and g[sponsor].fedoraRoleType.lower() == 'sponsor':
                raise ValueError, _('Sponsors cannot admin other sponsors')
            try:
                p.upgrade(groupName)
            except TypeError, e:
                turbogears.flash(_('Cannot upgrade %(name)s - %(error)s!') % {'name' : p.cn, 'error' : e})
                turbogears.redirect('viewGroup?groupName=%s' % group.cn)
            turbogears.flash(_('%s Upgraded!') % p.cn)
            turbogears.redirect('viewGroup?groupName=%s' % group.cn)


        # Downgrade user in a group
        elif action == 'downgrade':
            if g[userName].fedoraRoleType.lower() == 'administrator' and g[sponsor].fedoraRoleType.lower() == 'sponsor':
                raise ValueError, _('Sponsors cannot downgrade admins')
            try:
                p.downgrade(groupName)
            except TypeError, e:
                turbogears.flash(_('Cannot downgrade %(name)s - %(error)s!') % {'name' : p.cn, 'error' : e})
                turbogears.redirect('viewGroup?groupName=%s' % group.cn)
            turbogears.flash(_('%s Downgraded!') % p.cn)
            turbogears.redirect('viewGroup?groupName=%s' % group.cn)

        # Sponsor / Approve User
        elif action == 'sponsor' or action == 'apply':
            p.sponsor(groupName, sponsor)
            turbogears.flash(_('%s has been sponsored!') % p.cn)
            turbogears.redirect('viewGroup?groupName=%s' % group.cn)

        turbogears.flash(_('Invalid action: %s') % action)
        turbogears.redirect('viewGroup?groupName=%s' % group.cn)
        return dict()

    @expose(template='fas.templates.inviteMember')
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def inviteMember(self, name=None, email=None, skills=None):
        if name and email:
            turbogears.flash(_('Invitation Sent to: "%(name)s" <%(email)s>') % {'name' : name, 'email' : email})
        if name or email:#FIXME
            turbogears.flash(_('Please provide both an email address and the persons name.'))
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
                turbogears.flash(_('Application sent for %s') % user.cn)
            except ldap.ALREADY_EXISTS, e:
                turbogears.flash(_('Application Denied: %s') % e[0]['desc'])
            turbogears.redirect('viewGroup?groupName=%s' % group.cn)

        if action == 'Remove' and group.fedoraGroupUserCanRemove == 'TRUE':
            try:
                Groups.remove(group.cn, user.cn)
            except TypeError:
                turbogears.flash(_('%(user)s could not be removed from %(group)s!') % {'user' : user.cn, 'group' : group.cn})
                turbogears.redirect('viewGroup?groupName=%s' % group.cn)
            else:
                turbogears.flash(_('%(user)s removed from %(group)s!') % {'user' : user.cn, 'group' : group.cn})
                turbogears.redirect('viewGroup?groupName=%s' % group.cn)
        else:
            turbogears.flash(_('%s does not allow self removal') % group.cn)
            turbogears.redirect('viewGroup?groupName=%s' % group.cn)
        return dict()

    @expose(template='fas.templates.signUp')
    def signUp(self):
        if turbogears.identity.not_anonymous():
            turbogears.flash(_('No need to sign up, You have an account!'))
            turbogears.redirect('viewAccount')
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
            message = turbomail.Message('accounts@fedoraproject.org', p.mail, _('Fedora Project Password Reset'))
            message.plain = _("You have requested a password reset!  Your new password is - %s \nPlease go to https://admin.fedoraproject.org/fas/ to change it") % newpass['pass']
            turbomail.enqueue(message)
            p.__setattr__('userPassword', newpass['hash'])
            turbogears.flash(_('Your password has been emailed to you.  Please log in with it and change your password'))
            turbogears.redirect('/')

        except ldap.ALREADY_EXISTS:
            turbogears.flash(_('%s Already Exists, Please pick a different name') % cn)
            turbogears.redirect('signUp')
        return dict()

    @validate(form=editPersonForm)
    @error_handler(editAccount)
    @expose(template='fas.templates.editAccount')
    def editAccountSubmit(self, givenName, mail, fedoraPersonBugzillaMail, telephoneNumber, postalAddress, userName=None, fedoraPersonIrcNick='', fedoraPersonKeyId='', description=''):
        if userName:
            try:
                Groups.byUserName(turbogears.identity.current.user_name)[ADMINGROUP].cn
                if not userName:
                    userName = turbogears.identity.current.user_name
            except KeyError:
                turbogears.flash(_('You cannot view %s') % userName)
                userName = turbogears.identity.current.user_name
                turbogears.redirect("editAccount")
                return dict()
        else:
                userName = turbogears.identity.current.user_name
        user = Person.byUserName(userName)
        user.__setattr__('givenName', givenName.encode('utf8'))
        user.__setattr__('mail', mail.encode('utf8'))
        user.__setattr__('fedoraPersonBugzillaMail', fedoraPersonBugzillaMail.encode('utf8'))
        user.__setattr__('fedoraPersonIrcNick', fedoraPersonIrcNick.encode('utf8'))
        user.__setattr__('fedoraPersonKeyId', fedoraPersonKeyId.encode('utf8'))
        user.__setattr__('telephoneNumber', telephoneNumber.encode('utf8'))
        user.__setattr__('postalAddress', postalAddress.encode('utf8'))
        user.__setattr__('description', description.encode('utf8'))
        turbogears.flash(_('Your account has been updated.'))
        turbogears.redirect("viewAccount?userName=%s" % userName)
        return dict()

    @expose(format="json")
    def search(self, userName=None, groupName=None):
        people = Person.users('%s*' % userName)
        return dict(people=
                filter(lambda item: userName in item.lower(), people))


    @expose(template='fas.templates.invite')
    @exception_handler(errorMessage,rules="isinstance(tg_exceptions,ValueError)")
    @identity.require(identity.not_anonymous())
    def invite(self, target=None):
        import turbomail
        user = Person.byUserName(turbogears.identity.current.user_name)
        if target:
            message = turbomail.Message(user.mail, target, _('Come join The Fedora Project!'))
#            message.plain = "Please come join the fedora project!  Someone thinks your skills and abilities may be able to help our project.  If your interested please go to http://fedoraproject.org/wiki/HelpWanted"
            message.plain = _("%(name)s <%(email)s> has invited you to join the Fedora \
Project!  We are a community of users and developers who produce a \
complete operating system from entirely free and open source software \
(FOSS).  %(name)s thinks that you have knowledge and skills \
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
Fedora and FOSS are changing the world -- come be a part of it!") % {'name' : user.givenName, 'email' : user.mail}
            turbomail.enqueue(message)
            turbogears.flash(_('Message sent to: %s') % target)
        return dict(target=target, user=user)

def relativeUser(realUser, sudoUser):
    ''' Takes user and sees if they are allow to sudo for remote group'''
    p = Person.byUserName('realUser')

