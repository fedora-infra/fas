# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou
# Copyright © 2008-2010 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
#            Toshio Kuratomi <toshio@redhat.com>
#

# Does this need to come before the import turbogears or does it not matter?
try:
    from fedora.util import tg_url
except ImportError:
    from turbogears import url as tg_url

import turbogears
from turbogears import controllers, expose, identity, validate, validators, \
        error_handler, config
from turbogears.database import session

import cherrypy
import sqlalchemy
from sqlalchemy import select, func
from sqlalchemy.sql import and_

import re

import fas
from fas.model import People, PeopleTable, PersonRoles, PersonRolesTable, \
        Groups, GroupsTable, Log
from fas.auth import can_view_group, can_create_group, can_admin_group, \
        can_edit_group, can_apply_group, can_remove_user, can_upgrade_user, \
        can_sponsor_user, can_downgrade_user, is_approved

from fas.validators import UnknownGroup, KnownGroup, ValidGroupType, \
        ValidRoleSort, KnownUser

from fas.util import send_mail

class GroupView(validators.Schema):
    groupname = KnownGroup

class GroupMembers(validators.Schema):
    groupname = KnownGroup
    order_by = ValidRoleSort

class GroupCreate(validators.Schema):

    name = validators.All(
        UnknownGroup,
        validators.String(max=32, min=3),
        validators.Regex(regex='^[a-z0-9\-_]+$'),
        )
    display_name = validators.NotEmpty
    owner = validators.All(
        KnownUser,
        validators.NotEmpty,
        )
    prerequisite = KnownGroup
    group_type = ValidGroupType
    needs_sponsor = validators.Bool()
    user_can_remove = validators.Bool()
    invite_only = validators.Bool()

class GroupEdit(validators.Schema):
    groupname = KnownGroup

class GroupSave(validators.Schema):
    groupname = validators.All(KnownGroup, validators.String(max=32, min=2))
    display_name = validators.NotEmpty
    owner = KnownUser
    prerequisite = KnownGroup
    group_type = ValidGroupType
    invite_only = validators.Bool()

class GroupApply(validators.Schema):
    groupname = KnownGroup
    targetname = KnownUser

class GroupSponsor(validators.Schema):
    groupname = KnownGroup
    targetname = KnownUser

class GroupRemove(validators.Schema):
    groupname = KnownGroup
    targetname = KnownUser

class GroupUpgrade(validators.Schema):
    groupname = KnownGroup
    targetname = KnownUser

class GroupDowngrade(validators.Schema):
    groupname = KnownGroup
    targetname = KnownUser

class GroupInvite(validators.Schema):
    groupname = KnownGroup

class GroupSendInvite(validators.Schema):
    groupname = KnownGroup
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

    @expose(template="fas.templates.error", allow_json=True)
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupView())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.group.view", allow_json=True)
    def view(self, groupname, order_by='username'):
        '''View group'''
        sort_map = { 'username': 'people_1.username',
            'creation': 'person_roles_creation',
            'approval': 'person_roles_approval',
            'role_status': 'person_roles_role_status',
            'role_type': 'person_roles_role_type',
            'sponsor': 'people_2.username',
            }
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if not can_view_group(person, group):
            turbogears.flash(_("You cannot view '%s'") % group.name)
            turbogears.redirect('/group/list')
            return dict()

        # Also return information on who is not sponsored
        unsponsored = PersonRoles.query.join('group').join('member',
            aliased=True).outerjoin('sponsor', aliased=True).filter(
            and_(Groups.name==groupname,
                PersonRoles.role_status=='unapproved')).order_by(sort_map[order_by])
        unsponsored.json_props = {'PersonRoles': ['member']}
        return dict(group=group, sponsor_queue=unsponsored)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupMembers())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.group.members", allow_json=True)
    def members(self, groupname, search=u'a*', role_type=None,
                order_by='username'):
        '''View group'''
        sort_map = { 'username': 'people_1.username',
            'creation': 'person_roles_creation',
            'approval': 'person_roles_approval',
            'role_status': 'person_roles_role_status',
            'role_type': 'person_roles_role_type',
            'sponsor': 'people_2.username',
            }
        if not isinstance(search, unicode) and isinstance(search, basestring):
            search = unicode(search, 'utf-8', 'replace')

        re_search = search.translate({ord(u'*'): ur'%'}).lower()

        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if not can_view_group(person, group):
            turbogears.flash(_("You cannot view '%s'") % group.name)
            turbogears.redirect('/group/list')
            return dict()

        # return all members of this group that fit the search criteria
        members = PersonRoles.query.join('group').join('member', aliased=True).filter(
            People.username.like(re_search)
            ).outerjoin('sponsor', aliased=True).filter(
            Groups.name==groupname,
            ).order_by(sort_map[order_by])
        if role_type:
            members = members.filter(PersonRoles.role_type==role_type)
        group.json_props = {'PersonRoles': ['member']}
        return dict(group=group, members=members, search=search)

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.group.new")
    def new(self):
        '''Display create group form'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        if not can_create_group(person):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            turbogears.redirect('/')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupCreate())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.group.new", allow_json=True)
    def create(self, name, display_name, owner, group_type, invite_only=0,
               needs_sponsor=0, user_can_remove=1, prerequisite='', 
               joinmsg='', apply_rules='None'):
        '''Create a group'''

        groupname = name
        person = People.by_username(turbogears.identity.current.user_name)
        person_owner = People.by_username(owner)

        if not can_create_group(person):
            turbogears.flash(_('Only FAS adminstrators can create groups.'))
            turbogears.redirect('/')
        try:
            owner = People.by_username(owner)
            group = Groups()
            group.name = name
            group.display_name = display_name
            group.owner_id = person_owner.id
            group.group_type = group_type
            group.needs_sponsor = bool(needs_sponsor)
            if invite_only:
                group.invite_only = True
            else:
                group.invite_only = False
            group.user_can_remove = bool(user_can_remove)
            if prerequisite:
                prerequisite = Groups.by_name(prerequisite)
                group.prerequisite = prerequisite
            group.joinmsg = joinmsg
            group.apply_rules = apply_rules
            # Log group creation
            Log(author_id=person.id, description='%s created group %s' %
                (person.username, group.name))
            session.flush()
        except TypeError:
            turbogears.flash(_("The group: '%s' could not be created.") % groupname)
            return dict()
        else:
            try:
                owner.apply(group, person) # Apply...
                session.flush()
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
    @validate(validators=GroupEdit())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.group.edit")
    def edit(self, groupname):
        '''Display edit group form'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if not can_admin_group(person, group):
            turbogears.flash(_("You cannot edit '%s'.") % group.name)
            turbogears.redirect('/group/view/%s' % group.name)
        return dict(group=group)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupSave())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.group.edit")
    def save(self, groupname, display_name, owner, group_type, 
             needs_sponsor=0, user_can_remove=1, prerequisite='', 
             url='', mailing_list='', mailing_list_url='', invite_only=0,
             irc_channel='', irc_network='', joinmsg='', apply_rules="None"):
        '''Edit a group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if not can_edit_group(person, group):
            turbogears.flash(_("You cannot edit '%s'.") % group.name)
            turbogears.redirect('/group/view/%s' % group.name)
        else:
            try:
                owner = People.by_username(owner)
                group.display_name = display_name
                group.owner = owner
                group.group_type = group_type
                group.needs_sponsor = bool(needs_sponsor)
                group.user_can_remove = bool(user_can_remove)
                if prerequisite:
                    prerequisite = Groups.by_name(prerequisite)
                    group.prerequisite = prerequisite
                else:
                    group.prerequisite = None
                group.url = url
                group.mailing_list = mailing_list
                group.mailing_list_url = mailing_list_url
                if invite_only: 
                    group.invite_only = True
                else:
                    group.invite_only = False
                group.irc_channel = irc_channel
                group.irc_network = irc_network
                group.joinmsg = joinmsg
                group.apply_rules = apply_rules
                # Log here
                session.flush()
            except:
                turbogears.flash(_('The group details could not be saved.'))
            else:
                Log(author_id=person.id, description='%s edited group %s' %
                    (person.username, group.name))
                turbogears.flash(_('The group details have been saved.'))
                turbogears.redirect('/group/view/%s' % group.name)
            return dict(group=group)

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="genshi-text:fas.templates.group.list",
            as_format="plain", accept_format="text/plain",
            format="text", content_type='text/plain; charset=utf-8')
    @expose(template="fas.templates.group.list", allow_json=True)
    def list(self, search='*', with_members=True):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        memberships = {}
        groups = []
        re_search = re.sub(r'\*', r'%', search).lower()
        results = Groups.query.filter(Groups.name.like(re_search)).order_by('name').all()
        if self.jsonRequest():
            if with_members:
                membersql = sqlalchemy.select([PersonRoles.person_id, PersonRoles.group_id, PersonRoles.role_type], PersonRoles.role_status=='approved').order_by(PersonRoles.group_id)
                members = membersql.execute()
                for member in members:
                    try:
                        memberships[member[1]].append({'person_id': member[0], 'role_type': member[2]})
                    except KeyError:
                        memberships[member[1]]=[{'person_id': member[0], 'role_type': member[2]}]
            else:
                memberships = []
        for group in results:
            if can_view_group(person, group):
                groups.append(group)
        if not len(groups):
            turbogears.flash(_("No Groups found matching '%s'") % search)
        return dict(groups=groups, search=search, memberships=memberships)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupApply())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.group.apply')
    def application_screen(self, groupname, targetname=None):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if not targetname:
            targetname = username
            target = person
        else:
            target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if username != targetname or group.apply_rules is None or len(group.apply_rules) < 1:
            turbogears.redirect('/group/apply/%s/%s' % (group.name, target.username))

        if group in target.memberships:
            turbogears.flash('You are already a member of %s!' % group.name)
            turbogears.redirect('/group/view/%s' % group.name)

        if not can_apply_group(person, group, target):
            turbogears.flash(_('%(user)s can not apply to %(group)s.') % \
                {'user': target.username, 'group': group.name })
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()
        else:
            return dict(group=group)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupApply())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.group.view', allow_json=True)
    def apply(self, groupname, targetname=None):
        '''Apply to a group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if not targetname:
            target = person
        else:
            target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not can_apply_group(person, group, target):
            turbogears.flash(_('%(user)s can not apply to %(group)s.') % \
                {'user': target.username, 'group': group.name })
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()
        else:
            try:
                target.apply(group, person)
            except fas.ApplyError, e:
                turbogears.flash(_('%(user)s could not apply to %(group)s: %(error)s') % \
                    {'user': target.username, 'group': group.name, 'error': e})
                turbogears.redirect('/group/view/%s' % group.name)
            else:
                # TODO: Localize for each recipient.  This will require
                # some database calls so we'll also need to check whether it
                # makes things too slow.
                # Basic outline is:
                # for person_role in group.approved_roles:
                #     if person_role.role_type in ('administrator', 'sponsor'):
                #         sponsors_addr = p.member.email
                #         locale = p.member.locale or 'C'
                #         ## Do all the rest of the stuff to construct the
                #         ## email message -- the _(locale=locale) will
                #         ## translate the strings for that recipient
                #         send_mail(sponsors_addr, join_subject, join_text)
                # ## And if we still want to send this message to the user,
                # ## have to set locale = target.locale or 'C' and construct
                # ## the email one additional time and send to target.email
                locale = 'en'
                sponsor_url = config.get('base_url_filter.base_url') + \
                    tg_url('/group/view/%s' % groupname)
                sponsors_addr = '%(group)s-sponsors@%(host)s' % \
                    {'group': group.name, 'host': config.get('email_host')}
                sponsor_subject = _('Fedora \'%(group)s\' sponsor needed for %(user)s',
                        locale=locale) % {'user': target.username,
                                'group': group.name}
                sponsors_text = _('''
Fedora user %(user)s <%(email)s> has requested
membership for %(applicant)s in the %(group)s group and needs a sponsor.

Please go to %(url)s to take action.  
''', locale=locale) % { 'user': person.username,
        'applicant': target.username,
        'email': person.email,
        'url': sponsor_url,
        'group': group.name }

                join_subject = _('Application to the \'%(group)s\' group',
                        locale=locale) % {'user': target.username,
                                'group': group.name}
                join_text = _('''
Thank you for applying for the %(group)s group.  

%(joinmsg)s
''', locale=locale) % { 'user': person.username,
        'joinmsg': group.joinmsg,
        'group': group.name }

                send_mail(sponsors_addr, sponsor_subject, sponsors_text)
                send_mail(target.email, join_subject, join_text)

                Log(author_id=target.id, description='%s applied %s to %s' %
                    (person.username, target.username, group.name))

                turbogears.flash(_('%(user)s has applied to %(group)s!') % \
                    {'user': target.username, 'group': group.name})
                turbogears.redirect('/group/view/%s' % group.name)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupSponsor())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.group.view')
    def sponsor(self, groupname, targetname):
        '''Sponsor user'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not can_sponsor_user(person, group):
            turbogears.flash(_("You cannot sponsor '%s'") % target.username)
            turbogears.redirect('/group/view/%s' % group.name)
            return dict()
        else:
            try:
                target.sponsor(group, person)
            except fas.SponsorError, e:
                turbogears.flash(_("%(user)s could not be sponsored in %(group)s: %(error)s") % \
                    {'user': target.username, 'group': group.name, 'error': e})
                turbogears.redirect('/group/view/%s' % group.name)
            else:
                sponsor_subject = _('Your Fedora \'%s\' membership has been sponsored') % group.name
                sponsor_text = _('''
%(user)s <%(email)s> has sponsored you for membership in the %(group)s
group of the Fedora account system. If applicable, this change should
propagate into the e-mail aliases and git repository within an hour.
''') % {'group': group.name, 'user': person.username, 'email': person.email}

                send_mail(target.email, sponsor_subject, sponsor_text)

                Log(author_id=target.id, description='%s sponsored %s into %s' %
                    (person.username, target.username, group.name))

                turbogears.flash(_("'%s' has been sponsored!") % target.username)
                turbogears.redirect('/group/view/%s' % group.name)
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupRemove())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.group.view')
    def remove(self, groupname, targetname):
        '''Remove user from group'''
        # TODO: Add confirmation?
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not can_remove_user(person, group, target):
            turbogears.flash(_("You cannot remove '%(user)s' from '%(group)s'.") % \
                {'user': target.username, 'group': group.name})
            turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            return dict()
        else:
            try:
                target.remove(group, target)
            except fas.RemoveError, e:
                turbogears.flash(_("%(user)s could not be removed from %(group)s: %(error)s") % \
                    {'user': target.username, 'group': group.name, 'error': e})
                turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            else:
                removal_subject = _('Your Fedora \'%s\' membership has been removed') % group.name
                removal_text = _('''
%(user)s <%(email)s> has removed you from the '%(group)s'
group of the Fedora Accounts System This change is effective
immediately for new operations, and should propagate into the e-mail
aliases within an hour.
''') % {'group': group.name, 'user': person.username, 'email': person.email}

                send_mail(target.email, removal_subject, removal_text)

                Log(author_id=target.id, description='%s removed %s from %s' %
                    (person.username, target.username, group.name))

                turbogears.flash(_('%(name)s has been removed from %(group)s') % \
                    {'name': target.username, 'group': group.name})
                turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupUpgrade())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.group.view')
    def upgrade(self, groupname, targetname):
        '''Upgrade user in group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not can_upgrade_user(person, group):
            turbogears.flash(_("You cannot upgrade '%s'") % target.username)
            turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            return dict()
        else:
            try:
                target.upgrade(group, person)
            except fas.UpgradeError, e:
                turbogears.flash(_('%(name)s could not be upgraded in %(group)s: %(error)s') % \
                    {'name': target.username, 'group': group.name, 'error': e})
                turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            else:
                upgrade_subject = _('Your Fedora \'%s\' membership has been upgraded') % group.name

                # Should we make person.upgrade return this?
                role = PersonRoles.query.filter_by(group=group, member=target).one()
                status = role.role_type

                upgrade_text = _('''
%(user)s <%(email)s> has upgraded you to %(status)s status in the
'%(group)s' group of the Fedora Accounts System This change is
effective immediately for new operations, and should propagate
into the e-mail aliases within an hour.
''') % {'group': group.name, 'user': person.username, 'email': person.email, 'status': status}

                send_mail(target.email, upgrade_subject, upgrade_text)

                Log(author_id=target.id, description='%s upgraded %s to %s in %s' %
                    (person.username, target.username, status, group.name))

                turbogears.flash(_('%s has been upgraded!') % target.username)
                turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=GroupDowngrade())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.group.view')
    def downgrade(self, groupname, targetname):
        '''Upgrade user in group'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        group = Groups.by_name(groupname)

        if not can_downgrade_user(person, group):
            turbogears.flash(_("You cannot downgrade '%s'") % target.username)
            turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            return dict()
        else:
            try:
                target.downgrade(group, person)
            except fas.DowngradeError, e:
                turbogears.flash(_('%(name)s could not be downgraded in %(group)s: %(error)s') % \
                    {'name': target.username, 'group': group.name, 'error': e})
                turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            else:
                downgrade_subject = _('Your Fedora \'%s\' membership has been downgraded') % group.name

                role = PersonRoles.query.filter_by(group=group, member=target).one()
                status = role.role_type

                downgrade_text = _('''
%(user)s <%(email)s> has downgraded you to %(status)s status in the
'%(group)s' group of the Fedora Accounts System This change is
effective immediately for new operations, and should propagate
into the e-mail aliases within an hour.
''') % {'group': group.name, 'user': person.username, 'email': person.email, 'status': status}

                send_mail(target.email, downgrade_subject, downgrade_text)

                Log(author_id=target.id, description='%s downgraded %s to %s in %s' %
                    (person.username, target.username, status, group.name))

                turbogears.flash(_('%s has been downgraded!') % target.username)
                turbogears.redirect(cherrypy.request.headerMap.get("Referer", "/"))
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="genshi-text:fas.templates.group.dump", format="text",
            content_type='text/plain; charset=utf-8')
    @expose(allow_json=True)
    def dump(self, groupname=None, role_type=None):
        if not groupname:
            stmt = select([People.privacy, People.username, People.email,
                People.human_name, "'user'", 's.sponsored'],
                from_obj=PeopleTable.outerjoin(select([PersonRoles.sponsor_id,
                        func.count(PersonRoles.sponsor_id).label('sponsored')]
                        ).group_by(PersonRoles.sponsor_id
                            ).correlate().alias('s')
                )).order_by(People.username)
        else:
            stmt = select([People.privacy, People.username, People.email,
                People.human_name, PersonRoles.role_type, 's.sponsored'],
                from_obj=GroupsTable.join(PersonRolesTable).join(PeopleTable,
                    onclause=PeopleTable.c.id==PersonRolesTable.c.person_id
                    ).outerjoin(select([PersonRoles.sponsor_id,
                        func.count(PersonRoles.sponsor_id).label('sponsored')]
                        ).where(and_(
                            PersonRoles.group_id==Groups.id,
                            Groups.name==groupname)).group_by(
                                PersonRoles.sponsor_id).correlate().alias('s')
                            )).where(and_(Groups.name==groupname,
                                PersonRoles.role_status=='approved')
                                ).order_by(People.username)

        people = []
        if identity.in_any_group(config.get('admingroup', 'accounts'),
                config.get('systemgroup', 'fas-system')):
            user = 'admin'
        elif identity.current.anonymous:
            user = 'anonymous'
        else:
            user = 'public'
            username = identity.current.user_name

        for row in stmt.execute():
            person = list(row[1:])
            if not row['sponsored']:
                person[-1] = 0
            if row['privacy'] and user != 'admin' \
                    and username != row['username']:
                # filter private data
                person[2] = u''
            people.append(person)
        return dict(people=people)

    @identity.require(identity.not_anonymous())
    @validate(validators=GroupInvite())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.group.invite')
    def invite(self, groupname):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        person = person.filter_private()
        return dict(person=person, group=group)

    @identity.require(identity.not_anonymous())
    @validate(validators=GroupSendInvite())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.group.invite')
    def sendinvite(self, groupname, target):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        group = Groups.by_name(groupname)

        if is_approved(person, group):
            ### TODO: Make these translatable.  This will require taking
            # a parameter to determine which language to send in.  Allow the
            # user who is sending the invite to select a language since we
            # figure that they know what the proper language will be.for the
            # person they are sending to.
            invite_subject = ('Come join The Fedora Project!')
            invite_text = ('''
%(user)s <%(email)s> has invited you to join the Fedora
Project!  We are a community of users and developers who produce a
complete operating system from entirely free and open source software
(FOSS).  %(user)s thinks that you have knowledge and skills
that make you a great fit for the Fedora community, and that you might
be interested in contributing.

How could you team up with the Fedora community to use and develop your
skills?  Check out http://fedoraproject.org/join-fedora for some ideas.
Our community is more than just software developers -- we also have a
place for you whether you're an artist, a web site builder, a writer, or
a people person.  You'll grow and learn as you work on a team with other
very smart and talented people.

Fedora and FOSS are changing the world -- come be a part of it!''') % \
    {'user': person.username, 'email': person.email}

            send_mail(target, invite_subject, invite_text)

            turbogears.flash(_('Message sent to: %s') % target)
            turbogears.redirect('/group/view/%s' % group.name)
        else:
            turbogears.flash(_("You are not in the '%s' group.") % group.name)

        person = person.filter_private()
        return dict(target=target, person=person, group=group)
