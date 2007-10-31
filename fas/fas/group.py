import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler

import ldap
import cherrypy

import fas.fasLDAP

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

from fas.auth import *

from fas.user import knownUser, userNameExists

from textwrap import dedent

class knownGroup(validators.FancyValidator):
    '''Make sure that a group already exists'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        g = Groups.groups(value)
        if not g:
            raise validators.Invalid(_("The group '%s' does not exist.") % value, value, state)

class groupsExist(validators.FancyValidator):
    '''Make sure that required groups already exist'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        for group in value.split():
            g = Groups.groups(group)
            if not g:
                raise validators.Invalid(_("The required group '%s' does not exist.") % value, value, state)

class unknownGroup(validators.FancyValidator):
    '''Make sure that a group doesn't already exist'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        g = Groups.groups(value)
        if g:
            raise validators.Invalid(_("The group '%s' already exists.") % value, value, state)

class createGroup(validators.Schema):
    groupName = validators.All(unknownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    fedoraGroupDesc = validators.NotEmpty
    fedoraGroupOwner = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))
    fedoraGroupRequires = groupsExist

class editGroup(validators.Schema):
    groupName = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    fedoraGroupDesc = validators.NotEmpty
    fedoraGroupOwner = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))
    fedoraGroupRequires = groupsExist

class userNameGroupNameExists(validators.Schema):
    groupName = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    userName = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))

class groupNameExists(validators.Schema):
    groupName = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))

class groupInvite(validators.Schema):
    groupName = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    target = validators.Email(not_empty=True, strip=True),

#class findUser(widgets.WidgetsList): 
#    userName = widgets.AutoCompleteField(label=_('Username'), search_controller='search', search_param='userName', result_name='people')   
#    action = widgets.HiddenField(default='apply', validator=validators.String(not_empty=True)) 
#    groupName = widgets.HiddenField(validator=validators.String(not_empty=True)) 
#
#findUserForm = widgets.ListForm(fields=findUser(), submit_text=_('Invite')) 

class Group(controllers.Controller):

    def __init__(self):
        '''Create a Group Controller.'''

    @identity.require(turbogears.identity.not_anonymous())
    def index(self):
        '''Perhaps show a nice explanatory message about groups here?'''
        return dict()

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
    @validate(validators=groupNameExists())
    @error_handler(error)
    @expose(template="fas.templates.group.view")
    def view(self, groupName):
        '''View group'''
        userName = turbogears.identity.current.user_name
        if not canViewGroup(userName, groupName):
            turbogears.flash(_("You cannot view '%s'") % groupName)
            turbogears.redirect('/group/list')
            return dict()
        else:
            groups = Groups.byGroupName(groupName, includeUnapproved=True)
            group = Groups.groups(groupName)[groupName]
            userName = turbogears.identity.current.user_name
            try:
                myStatus = groups[userName].fedoraRoleStatus
            except KeyError:
                # Not in group
                myStatus = 'Not a Member' # This _has_ to stay 'Not a Member'
            except TypeError:
                groups = {}
            try:
                me = groups[userName]
            except:
                me = UserGroup()
            return dict(userName=userName, groups=groups, group=group, me=me)

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.group.new")
    def new(self):
        '''Display create group form'''
        userName = turbogears.identity.current.user_name
        if not canCreateGroup(userName):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            turbogears.redirect('/')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=createGroup())
    @error_handler(error)
    @expose(template="fas.templates.group.new")
    def create(self, groupName, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupNeedsSponsor='FALSE', fedoraGroupUserCanRemove='FALSE', fedoraGroupRequires='', fedoraGroupJoinMsg=''):
        '''Create a group'''
        userName = turbogears.identity.current.user_name
        if not canCreateGroup(userName):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            turbogears.redirect('/')
        try:
            fas.fasLDAP.Group.newGroup(groupName,
                                       fedoraGroupDesc,
                                       fedoraGroupOwner,
                                       fedoraGroupNeedsSponsor,
                                       fedoraGroupUserCanRemove,
                                       fedoraGroupRequires,
                                       fedoraGroupJoinMsg)
        except:
            turbogears.flash(_("The group: '%s' could not be created.") % groupName)
            return dict()
        else:
            try:
                p = Person.byUserName(fedoraGroupOwner) 
                Groups.apply(groupName, fedoraGroupOwner) # Apply...
                p.sponsor(groupName, userName) # Approve...
                p.upgrade(groupName) # Sponsor...
                p.upgrade(groupName) # Admin!
            except:
                turbogears.flash(_("The group: '%(group)s' has been created, but '%(user)s' could not be added as a group administrator.") % {'group': groupName, 'user': fedoraGroupOwner})
            else:
                turbogears.flash(_("The group: '%s' has been created.") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=groupNameExists())
    @error_handler(error)
    @expose(template="fas.templates.group.edit")
    def edit(self, groupName):
        '''Display edit group form'''
        userName = turbogears.identity.current.user_name
        if not canAdminGroup(userName, groupName):
            turbogears.flash(_("You cannot edit '%s'.") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        group = Groups.groups(groupName)[groupName]
        return dict(group=group)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=editGroup())
    @error_handler(error)
    @expose()
    def save(self, groupName, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupType=1, fedoraGroupNeedsSponsor="FALSE", fedoraGroupUserCanRemove="FALSE", fedoraGroupRequires="", fedoraGroupJoinMsg=""):
        '''Edit a group'''
        userName = turbogears.identity.current.user_name
        if fedoraGroupRequires is None:
            fedoraGroupRequires = ""
        if not canEditGroup(userName, groupName):
            turbogears.flash(_("You cannot edit '%s'.") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        # TODO: This is kind of an ugly hack.
        else:
            try:
                base = 'cn=%s,ou=FedoraGroups,dc=fedoraproject,dc=org' % groupName
                server = fas.fasLDAP.Server()
                server.modify(base, 'fedoraGroupDesc', fedoraGroupDesc)
                server.modify(base, 'fedoraGroupOwner', fedoraGroupOwner)
                server.modify(base, 'fedoraGroupType', fedoraGroupType)
                server.modify(base, 'fedoraGroupNeedsSponsor', fedoraGroupNeedsSponsor)
                server.modify(base, 'fedoraGroupUserCanRemove', fedoraGroupUserCanRemove)
                server.modify(base, 'fedoraGroupRequires', fedoraGroupRequires)
                server.modify(base, 'fedoraGroupJoinMsg', fedoraGroupJoinMsg)
            except:
                turbogears.flash(_('The group details could not be saved.'))
            else:
                turbogears.flash(_('The group details have been saved.'))
                turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.group.list", allow_json=True)
    def list(self, search='*'):
        groups = Groups.groups(search)
        userName = turbogears.identity.current.user_name
        myGroups = Groups.byUserName(userName)
        try:
            groups.keys()
        except:
            turbogears.flash(_("No Groups found matching '%s'") % search)
            groups = {}
        if self.jsonRequest():
            return ({'groups': groups})
        return dict(groups=groups, search=search, myGroups=myGroups)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def apply(self, groupName, userName=None):
        '''Apply to a group'''
        applicant = turbogears.identity.current.user_name
        if not userName:
            userName = applicant
        if not canApplyGroup(applicant, groupName, userName):
            turbogears.flash(_('%(user)s could not apply to %(group)s!') % \
                {'user': userName, 'group': groupName})
            turbogears.redirect('/group/view/%s' % groupName)
            return dict()
        else:
            try:
                Groups.apply(groupName, userName)
            except ldap.ALREADY_EXISTS:
                turbogears.flash(_('%(user)s has already applied to %(group)s!') % \
                    {'user': userName, 'group': groupName})
            else:
                import turbomail
                message = turbomail.Message(config.get('accounts_mail'), '%s-sponsors@fedoraproject.org' % groupName, \
                    "Fedora '%(group)s' sponsor needed for %(user)s" % {'user': userName, 'group': groupName})
                user = Person.byUserName(userName)
                name = user.givenName
                email = user.mail
                url = config.get('base_url') + turbogears.url('/group/edit/%s' % groupName)
                message.plain = dedent('''
                    Fedora user %(user)s, aka %(name)s <%(email)s> has requested
                    membership in the web group and needs a sponsor.
    
                    Please go to %(url)s to take action.  
                    ''') % {'user': userName, 'name': name, 'email': email, 'url': url}
                turbomail.enqueue(message)
                turbogears.flash(_('%(user)s has applied to %(group)s!') % \
                    {'user': userName, 'group': groupName})
                turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def sponsor(self, groupName, userName):
        '''Sponsor user'''
        sponsor = turbogears.identity.current.user_name
        if not canSponsorUser(sponsor, groupName, userName):
            turbogears.flash(_("You cannot sponsor '%s'") % userName)
            turbogears.redirect('/group/view/%s' % groupName)
            return dict()
        else:
            p = Person.byUserName(userName)
            try:
                p.sponsor(groupName, sponsor)
            except:
                turbogears.flash(_("'%s' could not be sponsored!") % p.cn)
                turbogears.redirect('/group/view/%s' % groupName)
            else:
                user = Person.byUserName(sponsor)
                group = Groups.groups(groupName)[groupName]
                import turbomail
                message = turbomail.Message(config.get('accounts_mail'), p.mail, "Your Fedora '%s' membership has been sponsored" % groupName)
                message.plain = dedent('''
                    %(name)s <%(email)s> has sponsored you for membership in the %(group)s
                    group of the Fedora account system. If applicable, this change should
                    propagate into the e-mail aliases and CVS repository within an hour.

                    %(joinmsg)s
                    ''') % {'group': groupName, 'name': user.givenName, 'email': user.mail, 'joinmsg': group.fedoraGroupJoinMsg}
                turbomail.enqueue(message)
                turbogears.flash(_("'%s' has been sponsored!") % p.cn)
                turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def remove(self, groupName, userName):
        '''Remove user from group'''
        # TODO: Add confirmation?
        sponsor = turbogears.identity.current.user_name
        if not canRemoveUser(sponsor, groupName, userName):
            turbogears.flash(_("You cannot remove '%s'.") % userName)
            turbogears.redirect('/group/view/%s' % groupName)
            return dict()
        else:
            try:
                Groups.remove(groupName, userName)
            except:
                turbogears.flash(_('%(name)s could not be removed from %(group)s!') % \
                    {'name': userName, 'group': groupName})
                turbogears.redirect('/group/view/%s' % groupName)
            else:
                import turbomail
                sponsor = Person.byUserName(sponsor)
                user = Person.byUserName(userName)
                message = turbomail.Message(config.get('accounts_mail'), user.mail, "Your Fedora '%s' membership has been removed" % groupName)
                message.plain = dedent('''
                    %(name)s <%(email)s> has removed you from the '%(group)s'
                    group of the Fedora Accounts System This change is effective
                    immediately for new operations, and should propagate into the e-mail
                    aliases within an hour.
                    ''') % {'group': groupName, 'name': sponsor.name, 'email': sponsor.mail}
                turbomail.enqueue(message)
                turbogears.flash(_('%(name)s has been removed from %(group)s!') % \
                    {'name': userName, 'group': groupName})
                turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def upgrade(self, groupName, userName):
        '''Upgrade user in group'''
        sponsor = turbogears.identity.current.user_name
        if not canUpgradeUser(sponsor, groupName, userName):
            turbogears.flash(_("You cannot upgrade '%s'") % userName)
            turbogears.redirect('/group/view/%s' % groupName)
            return dict()
        else:
            p = Person.byUserName(userName)
            try:
                p.upgrade(groupName)
            except TypeError, e:
                turbogears.flash(e)
                turbogears.redirect('/group/view/%s' % groupName)
            except:
                turbogears.flash(_('%(name)s could not be upgraded!') % {'name' : userName})
                turbogears.redirect('/group/view/%s' % groupName)
            else:
                user = Person.byUserName(sponsor)
                group = Groups.groups(groupName)[groupName]
                import turbomail
                message = turbomail.Message(config.get('accounts_mail'), p.mail, "Your Fedora '%s' membership has been upgraded" % groupName)
                user = Person.byUserName(userName)
                g = Groups.byUserName(userName)
                status = g[groupName].fedoraRoleType.lower()
                message.plain = dedent('''
                    %(name)s <%(email)s> has upgraded you to %(status)s status in the
                    '%(group)s' group of the Fedora Accounts System This change is
                    effective immediately for new operations, and should propagate
                    into the e-mail aliases within an hour.
                    ''') % {'group': groupName, 'name': user.givenName, 'email': user.mail, 'status': status}
                turbomail.enqueue(message)
                turbogears.flash(_('%s has been upgraded!') % userName)
                turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def downgrade(self, groupName, userName):
        '''Upgrade user in group'''
        sponsor = turbogears.identity.current.user_name
        if not canDowngradeUser(sponsor, groupName, userName):
            turbogears.flash(_("You cannot downgrade '%s'") % userName)
            turbogears.redirect('/group/view/%s' % groupName)
            return dict()
        else:
            p = Person.byUserName(userName)
            try:
                p.downgrade(groupName)
            except TypeError, e:
                turbogears.flash(e)
                turbogears.redirect('/group/view/%s' % groupName)
            except:
                turbogears.flash(_('%(name)s could not be downgraded!') % {'name': userName})
                turbogears.redirect('/group/view/%s' % groupName)
            else:
                user = Person.byUserName(sponsor)
                group = Groups.groups(groupName)[groupName]
                import turbomail
                message = turbomail.Message(config.get('accounts_mail'), p.mail, "Your Fedora '%s' membership has been downgraded" % groupName)
                user = Person.byUserName(userName)
                name = user.givenName
                email = user.mail
                g = Groups.byUserName(userName)
                status = g[groupName].fedoraRoleType.lower()
                message.plain = dedent('''
                    %(name)s <%(email)s> has downgraded you to %(status)s status in the
                    '%(group)s' group of the Fedora Accounts System This change is
                    effective immediately for new operations, and should propagate
                    into the e-mail aliases within an hour.
                    ''') % {'group': groupName, 'name': name, 'email': email, 'status': status}
                turbomail.enqueue(message)
                turbogears.flash(_('%s has been downgraded!') % p.cn)
                turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=groupNameExists())
    @error_handler(error)
    @expose(template="genshi-text:fas.templates.group.dump", format="text", content_type='text/plain; charset=utf-8')
    def dump(self, groupName):
        userName = turbogears.identity.current.user_name
        if not canViewGroup(userName, groupName):
            turbogears.flash(_("You cannot view '%s'") % groupName)
            turbogears.redirect('/group/list')
            return dict()
        else:
            groups = Groups.byGroupName(groupName)
            return dict(groups=groups, Person=Person)

    @identity.require(identity.not_anonymous())
    @validate(validators=groupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.invite')
    def invite(self, groupName):
        userName = turbogears.identity.current.user_name
        user = Person.byUserName(userName)
        return dict(user=user, group=groupName)

    @identity.require(identity.not_anonymous())
    @validate(validators=groupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.invite')
    def sendinvite(self, groupName, target=None):
        import turbomail
        userName = turbogears.identity.current.user_name
        user = Person.byUserName(userName)
        if isApproved(userName, groupName):
            message = turbomail.Message(user.mail, target, _('Come join The Fedora Project!'))
            message.plain = _(dedent('''
                %(name)s <%(email)s> has invited you to join the Fedora
                Project!  We are a community of users and developers who produce a
                complete operating system from entirely free and open source software
                (FOSS).  %(name)s thinks that you have knowledge and skills
                that make you a great fit for the Fedora community, and that you might
                be interested in contributing.

                How could you team up with the Fedora community to use and develop your
                skills?  Check out http://fedoraproject.org/join-fedora for some ideas.
                Our community is more than just software developers -- we also have a
                place for you whether you're an artist, a web site builder, a writer, or
                a people person.  You'll grow and learn as you work on a team with other
                very smart and talented people.

                Fedora and FOSS are changing the world -- come be a part of it!''')) % {'name': user.givenName, 'email': user.mail}
            turbomail.enqueue(message)
            turbogears.flash(_('Message sent to: %s') % target)
            turbogears.redirect('/group/view/%s' % groupName)
        else:
            turbogears.flash(_("You are not in the '%s' group.") % groupName)
        return dict(target=target, user=user)

