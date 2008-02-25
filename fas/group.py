import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import ldap
import cherrypy

import fas.fasLDAP

#from fas.fasLDAP import UserAccount
#from fas.fasLDAP import Person
#from fas.fasLDAP import Groups
#from fas.fasLDAP import UserGroup

from fas.auth import *

from fas.user import knownUser, usernameExists

from textwrap import dedent

import re

class knownGroup(validators.FancyValidator):
    '''Make sure that a group already exists'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        try:
            g = Groups.by_name(value)
        except InvalidRequestError:
            raise validators.Invalid(_("The group '%s' does not exist.") % value, value, state)

class unknownGroup(validators.FancyValidator):
    '''Make sure that a group doesn't already exist'''
    def _to_python(self, value, state):
        return value.strip()
    def validate_python(self, value, state):
        try:
            g = Groups.by_name(value)
        except InvalidRequestError:
            pass
        else:
            raise validators.Invalid(_("The group '%s' already exists.") % value, value, state)

class createGroup(validators.Schema):
    name = validators.All(unknownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    display_name = validators.NotEmpty
    owner = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))
    prerequisite = knownGroup
    #group_type = something

class editGroup(validators.Schema):
    groupname = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    display_name = validators.NotEmpty
    owner = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))
    prerequisite = knownGroup
    #group_type = something

class usernameGroupnameExists(validators.Schema):
    groupname = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    username = validators.All(knownUser(not_empty=True, max=10), validators.String(max=32, min=3))

class groupnameExists(validators.Schema):
    groupname = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))

class groupInvite(validators.Schema):
    groupname = validators.All(knownGroup(not_empty=True, max=10), validators.String(max=32, min=3))
    target = validators.Email(not_empty=True, strip=True),

#class findUser(widgets.WidgetsList): 
#    username = widgets.AutoCompleteField(label=_('Username'), search_controller='search', search_param='username', result_name='people')   
#    action = widgets.HiddenField(default='apply', validator=validators.String(not_empty=True)) 
#    groupname = widgets.HiddenField(validator=validators.String(not_empty=True)) 
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

    @expose(format="json")
    def exportShellAccounts(self):
        ''' Replaces old "exportShellAccounts.py" '''
        # TODO: Restrict access to this.
        group = Groups.by_name('sysadmin-main')
        users = {}
        for role in userlist.roles:
            if role.status == 'approved':
                person = role.member
                users[person.username] = {
                    'password' : u.password,
                    'ssh_key' : u.ssh_key,
                }
        groups = Groups.query.all()
        return dict(users=users, groups=groups)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=groupnameExists())
    @error_handler(error)
    @expose(template="fas.templates.group.view")
    def view(self, groupname):
        '''View group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if not canViewGroup(person, group):
            turbogears.flash(_("You cannot view '%s'") % group.name)
            turbogears.redirect('/group/list')
            return dict()
        else:
            return dict(person=person, group=group)

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.group.new")
    def new(self):
        '''Display create group form'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        if not canCreateGroup(person, Groups.by_name(config.get('admingroup'))):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            turbogears.redirect('/')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=createGroup())
    @error_handler(error)
    @expose(template="fas.templates.group.new")
    def create(self, name, display_name, owner, group_type, needs_sponsor=0, user_can_remove=1, prerequisite='', joinmsg=''):
        '''Create a group'''
        
        groupname = name
        person = People.by_username(turbogears.identity.current.user_name)
        person_owner = People.by_username(owner)

        if not canCreateGroup(person, Groups.by_name(config.get('admingroup'))):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            turbogears.redirect('/')
        try:
            owner = People.by_username(owner)
            group = Groups()
            group.name = name
            group.display_name = display_name
            group.owner_id = person_owner.id
            group.group_type = group_type
            group.needs_sponsor = needs_sponsor
            group.user_can_remove = user_can_remove
            if prerequisite:
                prerequisite = Groups.by_name(prerequisite)
                group.prerequisite = prerequisite
            group.joinmsg = joinmsg
            # Log here
            session.flush()
        except TypeError:
            turbogears.flash(_("The group: '%s' could not be created.") % groupname)
            return dict()
        else:
            try:
                session.flush()
                owner.apply(group, person) # Apply...
                owner.sponsor(group, person)
                owner.upgrade(group, person)
                owner.upgrade(group, person)
            except KeyError:
                turbogears.flash(_("The group: '%(group)s' has been created, but '%(user)s' could not be added as a group administrator.") % {'group': group.name, 'user': owner.username})
            else:
                turbogears.flash(_("The group: '%s' has been created.") % group.name)
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=groupnameExists())
    @error_handler(error)
    @expose(template="fas.templates.group.edit")
    def edit(self, groupname):
        '''Display edit group form'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if not canAdminGroup(person, group):
            turbogears.flash(_("You cannot edit '%s'.") % group.name)
            turbogears.redirect('/group/view/%s' % group.name)
        return dict(group=group)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=editGroup())
    @error_handler(error)
    @expose()
    def save(self, groupname, display_name, owner, group_type, needs_sponsor=0, user_can_remove=1, prerequisite='', joinmsg=''):
        '''Edit a group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if not canEditGroup(person, group):
            turbogears.flash(_("You cannot edit '%s'.") % group.name)
            turbogears.redirect('/group/view/%s' % group.name)
        else:
            try:
                owner = People.by_username(owner)
                group.display_name = display_name
                group.owner = owner
                group.group_type = group_type
                group.needs_sponsor = needs_sponsor
                group.user_can_remove = user_can_remove
                if prerequisite:
                    prerequisite = Groups.by_name(prerequisite)
                    group.prerequisite = prerequisite
                group.joinmsg = joinmsg
                # Log here
                session.flush()
            except:
                turbogears.flash(_('The group details could not be saved.'))
            else:
                turbogears.flash(_('The group details have been saved.'))
                turbogears.redirect('/group/view/%s' % groupname)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.group.list", allow_json=True)
    def list(self, search='*'):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        re_search = re.sub(r'\*', r'%', search).lower()
        groups = Groups.query.filter(Groups.name.like(re_search)).order_by('name')
        if groups.count() <= 0:
            turbogears.flash(_("No Groups found matching '%s'") % search)
            groups = {}
        if self.jsonRequest():
            return ({'groups': groups})
        return dict(groups=groups, search=search, person=person)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=usernameGroupnameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def apply(self, groupname, targetname=None):
        '''Apply to a group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if not targetname:
            target = person
        else:
            target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not canApplyGroup(person, group, target):
            turbogears.flash(_('%(user)s could not apply to %(group)s.') % \
                {'user': target.username, 'group': group.name })
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()
        else:
            try:
                target.apply(group, person)
            except: # TODO: More specific exception here.
                turbogears.flash(_('%(user)s has already applied to %(group)s!') % \
                    {'user': target.username, 'group': group.name})
            else:
                import turbomail
                # TODO: CC to right place, put a bit more thought into how to most elegantly do this
                message = turbomail.Message(config.get('accounts_mail'), '%s-sponsors@fedoraproject.org' % group.name, \
                    "Fedora '%(group)s' sponsor needed for %(user)s" % {'user': target.username, 'group': group.name})
                url = config.get('base_url') + turbogears.url('/group/edit/%s' % groupname)
                message.plain = dedent('''
                    Fedora user %(user)s, aka %(name)s <%(email)s> has requested
                    membership for %(applicant) (%(applicant_name)) in the %(group) group and needs a sponsor.
    
                    Please go to %(url)s to take action.  
                    ''') % {'user': person.username, 'name': person.human_name, 'applicant': target.username, 'applicant_name': target.human_name, 'email': person.emails['primary'].email, 'url': url}
                turbomail.enqueue(message)
                turbogears.flash(_('%(user)s has applied to %(group)s!') % \
                    {'user': target.username, 'group': group.name})
                turbogears.redirect('/group/view/%s' % group.name)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=usernameGroupnameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def sponsor(self, groupname, targetname):
        '''Sponsor user'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not canSponsorUser(sponsor, group, target):
            turbogears.flash(_("You cannot sponsor '%s'") % target.username)
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()
        else:
            try:
                group.sponsor_person(person, target)
            except:
                turbogears.flash(_("'%s' could not be sponsored!") % target.username)
                turbogears.redirect('/group/view/%s' % group.name)
            else:
                import turbomail
                message = turbomail.Message(config.get('accounts_mail'), p.mail, "Your Fedora '%s' membership has been sponsored" % group.name)
                message.plain = dedent('''
                    %(name)s <%(email)s> has sponsored you for membership in the %(group)s
                    group of the Fedora account system. If applicable, this change should
                    propagate into the e-mail aliases and CVS repository within an hour.

                    %(joinmsg)s
                    ''') % {'group': group.name, 'name': user.human_name, 'email': user.emails['primary'].email, 'joinmsg': group.joinmsg}
                turbomail.enqueue(message)
                turbogears.flash(_("'%s' has been sponsored!") % person.human_name)
                turbogears.redirect('/group/view/%s' % group.name)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=usernameGroupnameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def remove(self, groupname, targetname):
        '''Remove user from group'''
        # TODO: Add confirmation?
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not canRemoveUser(person, group, target):
            turbogears.flash(_("You cannot remove '%s'.") % target.username)
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()
        else:
            try:
                group.remove_person(person, target)
            except:
                turbogears.flash(_('%(name)s could not be removed from %(group)s!') % \
                    {'name': target.username, 'group': group.name})
                turbogears.redirect('/group/view/%s' % group.name)
            else:
                import turbomail
                message = turbomail.Message(config.get('accounts_mail'), target.emails['primary'].email, "Your Fedora '%s' membership has been removed" % group.name)
                message.plain = dedent('''
                    %(name)s <%(email)s> has removed you from the '%(group)s'
                    group of the Fedora Accounts System This change is effective
                    immediately for new operations, and should propagate into the e-mail
                    aliases within an hour.
                    ''') % {'group': group.name, 'name': person.human_name, 'email': person.emails['primary'].email}
                turbomail.enqueue(message)
                turbogears.flash(_('%(name)s has been removed from %(group)s!') % \
                    {'name': target.username, 'group': group.name})
                turbogears.redirect('/group/view/%s' % group.name)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=usernameGroupnameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def upgrade(self, groupname, targetname):
        '''Upgrade user in group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not canUpgradeUser(person, group, target):
            turbogears.flash(_("You cannot upgrade '%s'") % target.username)
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()
        else:
            try:
                group.upgrade_person(person, target)
            except TypeError, e:
                turbogears.flash(e)
                turbogears.redirect('/group/view/%s' % group.name)
            except:
                turbogears.flash(_('%(name)s could not be upgraded!') % {'name' : target.username})
                turbogears.redirect('/group/view/%s' % group.name)
            else:
                import turbomail
                message = turbomail.Message(config.get('accounts_mail'), target.emails['primary'].email, "Your Fedora '%s' membership has been upgraded" % group.name)
                user = Person.byUsername(username)
                g = Groups.byUsername(username)
                # Should we make upgrade_person return this?
                role = PersonRoles.query.filter_by(group=group, member=target).one()
                status = role.role_type
                message.plain = dedent('''
                    %(name)s <%(email)s> has upgraded you to %(status)s status in the
                    '%(group)s' group of the Fedora Accounts System This change is
                    effective immediately for new operations, and should propagate
                    into the e-mail aliases within an hour.
                    ''') % {'group': group.name, 'name': person.human_name, 'email': person.emails['primary'].email, 'status': status}
                turbomail.enqueue(message)
                turbogears.flash(_('%s has been upgraded!') % person.username)
                turbogears.redirect('/group/view/%s' % group.name)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=usernameGroupnameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.view')
    def downgrade(self, groupname, username):
        '''Upgrade user in group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not canDowngradeUser(person, group, target):
            turbogears.flash(_("You cannot downgrade '%s'") % target.username)
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()
        else:
            try:
                group.downgrade_person(person, target)
            except:
                turbogears.flash(_('%(username)s could not be downgraded!') % {'username': target.username})
                turbogears.redirect('/group/view/%s' % group.name)
            else:
                import turbomail
                message = turbomail.Message(config.get('accounts_mail'), target.emails['primary'].email, "Your Fedora '%s' membership has been downgraded" % group.name)
                role = PersonRoles.query.filter_by(group=group, member=target).one()
                status = role.role_type
                message.plain = dedent('''
                    %(name)s <%(email)s> has downgraded you to %(status)s status in the
                    '%(group)s' group of the Fedora Accounts System This change is
                    effective immediately for new operations, and should propagate
                    into the e-mail aliases within an hour.
                    ''') % {'group': group.name, 'name': person.human_name, 'email': person.emails['primary'].email, 'status': status}
                turbomail.enqueue(message)
                turbogears.flash(_('%s has been downgraded!') % target.username)
                turbogears.redirect('/group/view/%s' % group.name)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=groupnameExists())
    @error_handler(error)
    @expose(template="genshi-text:fas.templates.group.dump", format="text", content_type='text/plain; charset=utf-8')
    def dump(self, groupname):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if not canViewGroup(person, group):
            turbogears.flash(_("You cannot view '%s'") % group.name)
            turbogears.redirect('/group/list')
            return dict()
        else:
            return dict(groups=groups)

    @identity.require(identity.not_anonymous())
    @validate(validators=groupnameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.invite')
    def invite(self, groupname):
        username = turbogears.identity.current.user_name
        person = Person.byUsername(username)
        group = Groups.by_name(groupname)

        return dict(person=person, group=group)

    @identity.require(identity.not_anonymous())
    @validate(validators=groupnameExists())
    @error_handler(error)
    @expose(template='fas.templates.group.invite')
    def sendinvite(self, groupname, target):
        import turbomail
        username = turbogears.identity.current.user_name
        person = Person.byUsername(username)
        group = Groups.by_name(groupname)

        if isApproved(person, group):
            message = turbomail.Message(person.emails['primary'].email, target, _('Come join The Fedora Project!'))
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

                Fedora and FOSS are changing the world -- come be a part of it!''')) % {'name': user.human_name, 'email': user.emails['primary'].email}
            turbomail.enqueue(message)
            turbogears.flash(_('Message sent to: %s') % target)
            turbogears.redirect('/group/view/%s' % group.name)
        else:
            turbogears.flash(_("You are not in the '%s' group.") % group.name)
        return dict(target=target, person=person)

