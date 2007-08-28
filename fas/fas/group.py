import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler

import ldap

import fas.fasLDAP

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

from fas.auth import isAdmin, canAdminGroup, canSponsorGroup, canEditUser

from fas.user import knownUser, userNameExists

class knownGroup(validators.FancyValidator):
    '''Make sure that a group already exists'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        g = Groups.groups(value)
        if not g:
            raise validators.Invalid(_("The group '%s' does not exist.") % value, value, state)

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

class editGroup(validators.Schema):
    groupName = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    fedoraGroupDesc = validators.NotEmpty
    fedoraGroupOwner = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))

class userNameGroupNameExists(validators.Schema):
    groupName = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    userName = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))

class groupNameExists(validators.Schema):
    groupName = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))

#class findUser(widgets.WidgetsList): 
#    userName = widgets.AutoCompleteField(label=_('Username'), search_controller='search', search_param='userName', result_name='people')   
#    action = widgets.HiddenField(default='apply', validator=validators.String(not_empty=True)) 
#    groupName = widgets.HiddenField(validator=validators.String(not_empty=True)) 
#
#findUserForm = widgets.ListForm(fields=findUser(), submit_text=_('Invite')) 

class Group(controllers.Controller):

    def __init__(self):
        '''Create a Group Controller.'''

    def index(self):
        '''Perhaps show a nice explanatory message about groups here?'''
        return dict()

    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @validate(validators=groupNameExists())
    @error_handler(error)
    @expose(template="fas.templates.group.view")
    @identity.require(turbogears.identity.not_anonymous())
    def view(self, groupName):
        '''View group'''
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
        #searchUserForm.groupName.display('group')
        #findUser.groupName.display(value='fff')
        value = {'groupName': groupName}
        return dict(userName=userName, groups=groups, group=group, me=me, value=value)

    @expose(template="fas.templates.group.new")
    @identity.require(turbogears.identity.not_anonymous())
    def new(self):
        '''Display create group form'''
        userName = turbogears.identity.current.user_name
        if not isAdmin(userName):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            turbogears.redirect('/')
        return dict()

    @validate(validators=createGroup())
    @error_handler(error)
    @expose(template="fas.templates.group.new")
    @identity.require(turbogears.identity.not_anonymous())
    def create(self, groupName, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupNeedsSponsor="FALSE", fedoraGroupUserCanRemove="FALSE", fedoraGroupJoinMsg=""):
        '''Create a group'''
        userName = turbogears.identity.current.user_name
        if not isAdmin(userName):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            turbogears.redirect('/')
        try:
            fas.fasLDAP.Group.newGroup(groupName.encode('utf8'),
                                       fedoraGroupDesc.encode('utf8'),
                                       fedoraGroupOwner.encode('utf8'),
                                       fedoraGroupNeedsSponsor.encode('utf8'),
                                       fedoraGroupUserCanRemove.encode('utf8'),
                                       fedoraGroupJoinMsg.encode('utf8'),)

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
                turbogears.flash(_("The group: '%(group)s' has been created, but '%(user)' could not be added as a group administrator.") % {'group': groupName, 'user': fedoraGroupOwner})
            else:
                turbogears.flash(_("The group: '%s' has been created.") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @expose(template="fas.templates.group.edit")
    @identity.require(turbogears.identity.not_anonymous())
    def edit(self, groupName):
        '''Display edit group form'''
        userName = turbogears.identity.current.user_name
        if not canAdminGroup(userName, groupName):
            turbogears.flash(_("You cannot edit '%s'.") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        group = Groups.groups(groupName)[groupName]
        value = {'groupName': groupName,
                 'fedoraGroupDesc': group.fedoraGroupDesc,
                 'fedoraGroupOwner': group.fedoraGroupOwner,
                 'fedoraGroupType': group.fedoraGroupType,
                 'fedoraGroupNeedsSponsor': (group.fedoraGroupNeedsSponsor.upper() == 'TRUE'),
                 'fedoraGroupUserCanRemove': (group.fedoraGroupUserCanRemove.upper() == 'TRUE'),
                 #'fedoraGroupRequires': group.fedoraGroupRequires,
                 'fedoraGroupJoinMsg': group.fedoraGroupJoinMsg, }
        return dict(value=value)

    @validate(validators=editGroup())
    @error_handler(error)
    @expose()
    @identity.require(turbogears.identity.not_anonymous())
    def save(self, groupName, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupType=1, fedoraGroupNeedsSponsor="FALSE", fedoraGroupUserCanRemove="FALSE", fedoraGroupJoinMsg=""):
        '''Edit a group'''
        userName = turbogears.identity.current.user_name
        if not canAdminGroup(userName, groupName):
            turbogears.flash(_("You cannot edit '%s'.") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        # TODO: This is kind of an ugly hack.
        base = 'cn=%s,ou=FedoraGroups,dc=fedoraproject,dc=org' % groupName
        try:
            fas.fasLDAP.modify(base, 'fedoraGroupDesc', fedoraGroupDesc.encode('utf8'))
            fas.fasLDAP.modify(base, 'fedoraGroupOwner', fedoraGroupOwner.encode('utf8'))
            fas.fasLDAP.modify(base, 'fedoraGroupType', str(fedoraGroupType).encode('utf8'))
            fas.fasLDAP.modify(base, 'fedoraGroupNeedsSponsor', fedoraGroupNeedsSponsor.encode('utf8'))
            fas.fasLDAP.modify(base, 'fedoraGroupUserCanRemove', fedoraGroupUserCanRemove.encode('utf8'))
            fas.fasLDAP.modify(base, 'fedoraGroupJoinMsg', fedoraGroupJoinMsg.encode('utf8'))
        except:
            turbogears.flash(_('The group details could not be saved.'))
            return dict()
        else:
            turbogears.flash(_('The group details have been saved.'))
            turbogears.redirect('/group/view/%s' % groupName)
            return dict()

    @expose(template="fas.templates.group.list")
    @identity.require(turbogears.identity.not_anonymous())
    def list(self, search='*'):
        groups = Groups.groups(search)
        userName = turbogears.identity.current.user_name
        myGroups = Groups.byUserName(userName)
        try:
            groups.keys()
        except:
            turbogears.flash(_("No Groups found matching '%s'") % search)
            groups = {}
        return dict(groups=groups, search=search, myGroups=myGroups)

    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    @identity.require(turbogears.identity.not_anonymous())
    def apply(self, groupName, userName):
        '''Apply to a group'''
        try:
            Groups.apply(groupName, userName)
        except ldap.ALREADY_EXISTS:
            turbogears.flash(_('%(user)s is already in %(group)s!') % {'user': userName, 'group': groupName})
            turbogears.redirect('/group/view/%s' % groupName)
        else:
            turbogears.flash(_('%(user)s has applied to %(group)s!') % {'user': userName, 'group': groupName})
            turbogears.redirect('/group/view/%s' % groupName)

    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    @identity.require(turbogears.identity.not_anonymous())
    def sponsor(self, groupName, userName):
        '''Sponsor user'''
        sponsor = turbogears.identity.current.user_name
        if not canSponsorGroup(sponsor, groupName):
            turbogears.flash(_("You are not a sponsor for '%s'") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        try:
            group = Groups.groups(groupName)[groupName]
        except KeyError:
            turbogears.flash(_('Group Error: %s does not exist.') % groupName)
            # The following line is kind of pointless- any suggestions?
            turbogears.redirect('/group/view/%s' % groupName)
        p = Person.byUserName(userName)
        g = Groups.byGroupName(groupName, includeUnapproved=True)
        # TODO: Check if the person actually applied to the group.
        p.sponsor(groupName, sponsor)
        turbogears.flash(_('%s has been sponsored!') % p.cn)
        turbogears.redirect('/group/view/%s' % groupName)

    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    @identity.require(turbogears.identity.not_anonymous())
    def remove(self, groupName, userName):
        '''Remove user from group'''
        # TODO: Add confirmation?
        sponsor = turbogears.identity.current.user_name
        if not canSponsorGroup(sponsor, groupName) \
            and sponsor != userName: # Users can remove themselves
            turbogears.flash(_("You are not a sponsor for '%s'") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        if canAdminGroup(userName, groupName) \
            and (not canAdminGroup(sponsor, groupName)):
            turbogears.flash(_('Sponsors cannot remove administrators.') % userName)
            turbogears.redirect('/group/view/%s' % groupName)
        try:
            Groups.remove(groupName, userName)
        except TypeError:
            turbogears.flash(_('%(name)s could not be removed from %(group)s!') % {'name': userName, 'group': groupName})
            turbogears.redirect('/group/view/%s' % groupName)
        else:
            turbogears.flash(_('%(name)s has been removed from %(group)s!') % {'name': userName, 'group': groupName})
            turbogears.redirect('/group/view/%s' % groupName)
        return dict()

    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    @identity.require(turbogears.identity.not_anonymous())
    def upgrade(self, groupName, userName):
        '''Upgrade user in group'''
        sponsor = turbogears.identity.current.user_name
        if not canSponsorGroup(sponsor, groupName):
            turbogears.flash(_("You are not a sponsor for '%s'") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        # This is already checked in fasLDAP.py
        #if canAdminGroup(userName, groupName):
        #    turbogears.flash(_('Group administators cannot be upgraded any further.'))
        #    turbogears.redirect('/group/view/%s' % groupName)
        elif canSponsorGroup(userName, groupName) \
            and (not canAdminGroup(sponsor, groupName)):
            turbogears.flash(_('Sponsors cannot upgrade other sponsors.') % userName)
            turbogears.redirect('/group/view/%s' % groupName)
        p = Person.byUserName(userName)
        try:
            p.upgrade(groupName)
        except:
            turbogears.flash(_('%(name)s could not be upgraded!') % userName)
            turbogears.redirect('/group/view/%s' % groupName)
        turbogears.flash(_('%s has been upgraded!') % userName)
        turbogears.redirect('/group/view/%s' % groupName)

    @validate(validators=userNameGroupNameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    @identity.require(turbogears.identity.not_anonymous())
    def downgrade(self, groupName, userName):
        '''Upgrade user in group'''
        sponsor = turbogears.identity.current.user_name
        if not canSponsorGroup(sponsor, groupName):
            turbogears.flash(_("You are not a sponsor for '%s'") % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        if canAdminGroup(userName, groupName) \
            and (not canAdminGroup(sponsor, groupName)):
            turbogears.flash(_('Sponsors cannot downgrade group administrators.') % userName)
            turbogears.redirect('/group/view/%s' % groupName)
        p = Person.byUserName(userName)
        try:
            p.upgrade(groupName)
        except:
            turbogears.flash(_('%(name)s could not be downgraded!') % userName)
            turbogears.redirect('/group/view/%s' % groupName)
        turbogears.flash(_('%s has been downgraded!') % p.cn)
        turbogears.redirect('/group/view/%s' % groupName)

    @validate(validators=groupNameExists())
    @error_handler(error)
    @expose(template="genshi-text:fas.templates.group.dump", format="text", content_type='text/plain; charset=utf-8')
    @identity.require(turbogears.identity.not_anonymous())
    def dump(self, groupName=None):
        groups = Groups.byGroupName(groupName)
        return dict(groups=groups, Person=Person)

