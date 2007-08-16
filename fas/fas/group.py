import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler

import ldap

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

from fas.auth import isAdmin, canAdminGroup, canSponsorGroup, canEditUser

from operator import itemgetter

from fas.user import knownUser

class knownGroup(validators.FancyValidator):
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        g = Groups.groups(groupName)
        if g:
            raise validators.Invalid(_("The group '%s' already exists") % value, value, state)

class unknownGroup(validators.FancyValidator):
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        g = Groups.groups(groupName)
        if not g:
            raise validators.Invalid(_("The group '%s' does not exist") % value, value, state)

class createGroup(widgets.WidgetsList):
    groupName = widgets.TextField(label=_('Group Name'), validator=validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3)))
    fedoraGroupDesc = widgets.TextField(label=_('Description'), validator=validators.NotEmpty)
    fedoraGroupOwner = widgets.TextField(label=_('Group Owner'), validator=validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3)))
    fedoraGroupNeedsSponsor = widgets.CheckBox(label=_('Needs Sponsor'))
    fedoraGroupUserCanRemove = widgets.CheckBox(label=_('Self Removal'))
    fedoraGroupJoinMsg = widgets.TextField(label=_('Group Join Message'))

createGroupForm = widgets.ListForm(fields=createGroup(), submit_text=_('Create'))

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

findUserForm = widgets.ListForm(fields=findUser(), submit_text=_('Invite')) 

class Group(controllers.Controller):

    def __init__(self):
        '''Create a Group Controller.'''

    def index(self):
        '''Perhaps show a nice explanatory message about groups here?'''
        return dict()

    @expose(template="fas.templates.group.view")
    @identity.require(turbogears.identity.not_anonymous())
    def view(self, groupName):
        '''View group'''
        # FIXME: Cleaner checks
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
        value = {'groupName': group.cn}
        groups = sorted(groups.items(), key=itemgetter(0))
        return dict(userName=userName, groups=groups, group=group, me=me, value=value)

    @expose(template="fas.templates.group.new")
    @identity.require(turbogears.identity.not_anonymous())
    def new(self, groupName):
        '''Create a group'''
        return dict()

    #@validate(form=createGroupForm)
    @expose(template="fas.templates.group.new")
    @identity.require(turbogears.identity.not_anonymous())
    def create(self, groupName, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupNeedsSponsor=True, fedoraGroupUserCanRemove=True, fedoraGroupJoinMsg=""):
        userName = turbogears.identity.current.user_name
        if not isAdmin(userName):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            # TODO: Create a general access denied/error page.
            turbogears.redirect('/')
        try:
            Groups.newGroup(groupName, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupNeedsSponsor, fedoraGroupUserCanRemove, fedoraGroupJoinMsg)
            turbogears.flash(_("The group: '%s' has been created.") % groupName)
            turbogears.redirect('/group/view/%s', groupName)
        except:
            turbogears.flash(_("The group: '%s' could not be created.") % groupName)
        return dict()

    @expose(template="fas.templates.group.edit")
    @identity.require(turbogears.identity.not_anonymous())
    def edit(self, groupName):
        '''Edit a group'''
        #TODO: Handle the "no such group" case (or maybe create
        #a generic function to check user/group existence.
        userName = turbogears.identity.current.user_name
        if not canAdminGroup(userName, groupName):
            turbogears.flash(_('You cannot edit %s') % groupName)
            turbogears.redirect('/group/view/%s' % groupName)
        group = Groups.groups(groupName)[groupName]
        value = {'groupName': groupName,
                  'fedoraGroupOwner': group.fedoraGroupOwner,
                  'fedoraGroupType': group.fedoraGroupType,
                  'fedoraGroupNeedsSponsor': (group.fedoraGroupNeedsSponsor.upper() == 'TRUE'),
                  'fedoraGroupUserCanRemove': (group.fedoraGroupUserCanRemove.upper() == 'TRUE'),
                  'fedoraGroupJoinMsg': group.fedoraGroupJoinMsg,
                  'fedoraGroupDesc': group.fedoraGroupDesc, }
                  #'fedoraGroupRequires': group.fedoraGroupRequires, }
        return dict(value=value)

    #@validate(form=editGroupForm)
    @expose(template="fas.templates.group.edit")
    @identity.require(turbogears.identity.not_anonymous())
    def save(self, stuff):
        #TODO
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
        groups = sorted(groups.items(), key=itemgetter(0))
        return dict(groups=groups, search=search, myGroups=myGroups)

    # TODO: Validate
    @expose(template='fas.templates.group.view')
    @identity.require(turbogears.identity.not_anonymous())
    def apply(self, groupName, userName):
        try:
            Groups.apply(groupName, userName)
        except ldap.ALREADY_EXISTS:
            turbogears.flash(_('%(user)s is already in %(group)s!') % {'user': userName, 'group': groupName})
            turbogears.redirect('/group/view/%s' % groupName)
        else:
            turbogears.flash(_('%(user)s has applied to %(group)s!') % {'user': userName, 'group': groupName})
            turbogears.redirect('/group/view/%s' % group.cn)

    # TODO: Validate (user doesn't exist case)
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

    # TODO: Validate (user doesn't exist case)
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

    # TODO: Validate (user doesn't exist case)
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

    # TODO: Validate (user doesn't exist case)
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

    # TODO: Validate (group doesn't exist case)
    @expose(template="genshi-text:fas.templates.group.dump", content_type='text/plain; charset=utf-8')
    @identity.require(turbogears.identity.not_anonymous())
    def dump(self, groupName=None):
        groups = Groups.byGroupName(groupName)
        groups = sorted(groups.items(), key=itemgetter(0))
        return dict(groups=groups, Person=Person)

