# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED

from fas.models import MembershipStatus
from fas.models import MembershipRole
from fas.models import AccountLogType

import fas.models.provider as provider
import fas.models.register as register

from fas.views import redirect_to
from fas.utils import compute_list_pages_from

from fas.forms.people import ContactInfosForm, PeopleForm
from fas.forms.la import SignLicenseForm
from fas.forms.group import EditGroupForm
from fas.forms.group import GroupAdminsForm

from fas.security import MembershipValidator
from fas.security import ParamsValidator

from fas.utils import _, Config
from fas.utils.fgithub import Github

from fas.notifications.email import Email

import mistune


class Groups(object):

    def __init__(self, request):
        self.request = request
        self.params = ParamsValidator(request)

    @view_config(route_name="groups", renderer='/groups/list.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    @view_config(route_name='groups-paging', renderer='/groups/list.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    def paging(self):
        """ Groups' list view with paging feature. """
        try:
            page = int(self.request.matchdict.get('pagenb', 1))
        except ValueError:
            return HTTPBadRequest()

        # TODO: still, get limit from config file or let user choose in between
        # TODO: predifined one?
        groups = provider.get_groups(50, page)
        cnt_groups = provider.get_groups(count=True)

        pages, count = compute_list_pages_from(cnt_groups, 50)

        if page > pages:
            return HTTPBadRequest()

        return dict(
            groups=groups,
            count=count,
            page=page,
            pages=pages
            )

    @view_config(
        route_name='group-search-rd', renderer='/group/search.xhtml')
    def search_redirect(self):
        """ Redirect the search to the proper url. """
        _id = self.request.params.get('q', '*')
        return redirect_to('/group/search/%s' % _id)

    @view_config(
        route_name='group-search', renderer='/groups/search.xhtml')
    @view_config(
        route_name='group-search-paging', renderer='/groups/search.xhtml')
    def search(self):
        """ Search groups. """
        try:
            _id = self.request.matchdict['pattern']
        except KeyError:
            return HTTPBadRequest()
        page = int(self.request.matchdict.get('pagenb', 1))

        grpname = None
        try:
            _id = int(_id)
        except:
            grpname = _id

        if grpname:
            if '*' in grpname:
                grpname = grpname.replace('*', '%')
            else:
                grpname = grpname + '%'
            groups = provider.get_groups(50, page, pattern=grpname)
            groups_cnt = provider.get_groups(pattern=grpname, count=True)
        else:
            groups = provider.get_group_by_id(_id)
            groups_cnt = 1

        if not groups:
            self.request.session.flash(
                _('No group found for the query: %s') % _id, 'error')
            return redirect_to('/groups')

        pages, count = compute_list_pages_from(groups_cnt, 50)

        if page > pages:
            return HTTPBadRequest()

        if grpname and len(groups) == 1 and page == 1:
            self.request.session.flash(
                _("Only one group matching, redirecting to the group's page"),
                'info')
            return redirect_to('/group/details/%s' % groups[0].id)

        return dict(
            groups=groups,
            page=page,
            pages=pages,
            count=count,
            pattern=_id
        )

    @view_config(route_name='group-details', renderer='/groups/details.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    def details(self):
        """ Group's details page."""
        try:
            _id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        limit = 50

        self.params.add_optional('members')
        self.params.add_optional('members_page')

        user_form = ContactInfosForm(self.request.POST, self.request.get_user)
        license_form = SignLicenseForm(self.request.POST)
        people_form = PeopleForm(self.request.POST)

        g_memberships = provider.get_group_membership(_id)

        group = g_memberships[0][0]
        memberships = []
        members = []
        user_members = []
        sponsor_members = []
        admin_members = []
        admin_form = None

        authenticated = self.request.get_user
        authenticated_membership = None
        is_member = False

        for group, membership, member in g_memberships:
            memberships.append(membership)
            if authenticated != member:
                if membership.get_status() == MembershipStatus.APPROVED:
                    if membership.role == MembershipRole.USER:
                        user_members.append(membership)
                    elif membership.role == MembershipRole.SPONSOR:
                        sponsor_members.append(membership)
                    elif membership.role == MembershipRole.ADMINISTRATOR:
                        admin_members.append(membership)
                    members.append(membership)
            else:
                authenticated = member
                authenticated_membership = membership
                if membership.get_status() == MembershipStatus.APPROVED:
                    is_member = True

        if authenticated:
            if authenticated.id == group.owner_id:
                admin_form = GroupAdminsForm(self.request.POST)
                admin_form.owner_id.choices = [
                    (person.people.id,
                        '%s (%s)' % (
                            person.people.username, person.people.fullname))
                    for person in admin_members]

        membership_request = provider.get_memberships_by_status(
            status=MembershipStatus.PENDING,
            group=group.id
            )

        license_signed_up = None
        if self.request.authenticated_userid:
            license_signed_up = provider.is_license_signed(
                group.license_sign_up, self.request.get_user.id)

        #FIXME: filter out members from people list.
        #people_form.people.choices = [
            #(u.id, u.username + ' (' + u.fullname + ')')
            #for u in provider.get_people()]

        # Disable paging on members list.
        # valid_member = self.request.get_user() in person
        # Disable paging for now
        # obj_start = 0
        # obj_max = limit
        page = 1
        # if params.is_valid():
            # page = int(params.get_optional('members_page')) or 1
            # if page > 1:
                # obj_max = (limit * page)
                # obj_start = (obj_max - limit) + 1
            # else:
                # obj_max = limit
                # obj_start = 0

        return dict(
            group=group,
            parent_group=group.parent_group,
            members=members,
            users=user_members,
            sponsors=sponsor_members,
            admin=admin_members,
            count=len(members),
            license_signed_up=license_signed_up,
            page=page,
            pages=int(len(members) / limit),
            person=authenticated,
            person_membership=authenticated_membership,
            is_member=is_member,
            membership_status=MembershipStatus,
            membership_request=membership_request,
            userform=user_form,
            licenseform=license_form,
            adminform=admin_form,
            peopleform=people_form,
            text=mistune
            )

    @view_config(route_name='group-edit', permission='group_edit',
                 renderer='/groups/edit.xhtml')
    def edit(self):
        """ group editor page."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        self.group = provider.get_group_by_id(self.id)

        ms = MembershipValidator(self.request.authenticated_userid,
            [self.group.name])
        # TODO: move this to Auth provider?
        # Prevent denied client from requesting direct url
        if not self.request.authenticated_is_admin():
            if not self.request.authenticated_is_modo():
                if not self.request.authenticated_is_group_admin(
                        self.group.name):
                    return redirect_to('/group/details/%s' % self.id)

        form = EditGroupForm(self.request.POST, self.group)

        # Group's name is not edit-able
        form.name.data = self.group.name

        # Remove group being edited from parent list if present
        parent_groups = provider.get_candidate_parent_groups()
        if self.group in parent_groups:
            parent_groups.remove((self.group.id, self.group.name))

        form.parent_group_id.choices = [
            (group.id, group.name) for group in parent_groups]
        form.parent_group_id.choices.insert(0, (-1, u'-- None --'))

        form.group_type.choices = [
            (t.id, t.name) for t in provider.get_group_types()]
        form.group_type.choices.insert(0, (-1, u'-- Select a group type --'))

        # TODO: Double check usage of QuerySelectField for those two instead
        if self.request.method is not 'POST':
            form.owner_id.choices.insert(0, (-1, u'-- Select a username --'))
            form.license_sign_up.choices.insert(0, (-1, u'-- None --'))

        if self.request.method == 'POST'\
                and ('form.save.group-details' in self.request.params):
            if form.validate():
                form.populate_obj(self.group)
                if form.bound_to_github.data and not self.group.bound_to_github:
                    g = Github()
                    g.create_group(
                        name=self.group.name,
                        repo=self.group.name,
                        access='push')
                return redirect_to('/group/details/%s' % self.id)

        return dict(form=form, id=self.id)


    @view_config(route_name='group-apply', permission='authenticated')
    def group_apply(self):
        """ Apply to a group."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        form = PeopleForm(self.request.POST)

        self.group = provider.get_group_by_id(self.id)
        user = self.request.get_user

        membership = provider.get_membership(
            user.username, self.group.name)

        email = Email('membership_update')

        can_apply = False
        if not membership:
            can_apply = True

        if self.group.license_sign_up > -1:
            if  provider.is_license_signed(
                self.group.license_sign_up, user.id):
                status = MembershipStatus.UNAPPROVED
                can_apply = False

        if self.request.method == 'POST':
            status = MembershipStatus.PENDING
            log = AccountLogType.ASKED_GROUP_MEMBERSHIP
            email.set_msg(
                topic='application',
                people=user,
                group=self.group,
                url=self.request.route_url(
                    'group-details', id=self.group.id))

            if not self.group.need_approval:
                status = MembershipStatus.APPROVED
                log = AccountLogType.NEW_GROUP_MEMBERSHIP
                email.set_msg(
                    topic='join',
                    people=user,
                    group=self.group,
                    url=self.request.route_url(
                        'group-details', id=self.group.id))

            if can_apply:
                register.add_membership(
                    self.group.id,
                    user.id,
                    status
                )
                register.save_account_activity(
                        self.request,
                        user.id,
                        log,
                        self.group.name)

                email.send(user.email)
            else:
                if membership.get_status() == MembershipStatus.APPROVED:
                    self.request.session.flash(
                        _("You are already a member of this group"), 'info')
                elif membership.get_status() == MembershipStatus.PENDING:
                    self.request.session.flash(
                        _("Your membership application already is pending"),
                        'info')
                elif membership.get_status() == MembershipStatus.UNAPPROVED:
                    self.request.session.flash(
                        _("Your membership application has been declined"),
                        'error')

        return redirect_to('/group/details/%s' % self.group.id)

    @view_config(route_name='group-action', permission='authenticated')
    def group_action(self):
        """ Upgrade or downgrade an user in a group."""
        if self.request.method == 'POST':
            form = PeopleForm(self.request.POST)

            group_id = self.request.POST.get('group_id')
            user_id = self.request.POST.get('user_id')
            reason = self.request.POST.get('msg_text')

            if form.validate():
                user_id = form.people.data

            self.group = provider.get_group_by_id(group_id)
            self.user = provider.get_people_by_id(user_id)

            if self.user:
                membership = provider.get_membership(
                    self.user.username, self.group.name)

            msg = ''
            email = Email('membership_update')
            log_type = None
            action = self.request.POST.get('action')

            if action == 'invite':
                invitee = self.request.POST.get('invitee')
                if invitee:
                    email.set_msg(
                        topic='invite',
                        people=self.request.get_user,
                        group=self.group,
                        organisation=Config.get('project.organisation'),
                        url=self.request.route_url(
                            'group-details', id=self.group.id))
                    email.send(invitee)
                msg = _(u'Invitation sent!')

            elif action == 'add':
                if form.validate():
                    register.add_membership(
                        self.group.id,
                        self.user.id,
                        MembershipStatus.APPROVED)
                    email.set_msg(
                        topic='join',
                        people=self.user,
                        group=self.group,
                        url=self.request.route_url(
                            'group-details', id=self.group.id))
                    msg = _(u'%s is now a member of your group'
                    % self.user.username)

            elif action == 'removal':
                log_type = AccountLogType.REVOKED_GROUP_MEMBERSHIP
                register.remove_membership(self.group.id, self.user.id)
                register.save_account_activity(
                    self.request,
                    self.user.id,
                    log_type,
                    self.group.name)
                email.set_msg(
                    topic='revoke',
                    body='body_self_removal',
                    people=self.user, group=self.group)
                msg = _(u'You are no longer a member of this group')

            elif action == 'upgrade':
                if membership.get_status() == MembershipStatus.PENDING:
                    membership.status = MembershipStatus.APPROVED
                    msg = _(u'User %s is now approved into the group %s' % (
                        self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.NEW_GROUP_MEMBERSHIP,
                        self.group.name)
                elif membership.get_role() == MembershipRole.USER:
                    membership.role = MembershipRole.EDITOR
                    msg = _(u'User %s is now EDITOR of the group '
                        '%s' % (self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.PROMOTED_GROUP_MEMBERSHIP,
                        'EDITOR: %s' % self.group.name)
                elif membership.get_role() == MembershipRole.EDITOR:
                    membership.role = MembershipRole.SPONSOR
                    msg = _(u'User %s is now SPONSOR of the group '
                        '%s' % (self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.PROMOTED_GROUP_MEMBERSHIP,
                        'SPONSOR: %s' % self.group.name)
                elif membership.get_role() == MembershipRole.SPONSOR:
                    membership.role = MembershipRole.ADMINISTRATOR
                    msg = _(u'User %s is now ADMINISTRATOR of the '
                        'group %s' % (self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.PROMOTED_GROUP_MEMBERSHIP,
                        'ADMINISTRATOR: %s' % self.group.name)

                email.set_msg(
                    topic='upgrade',
                    people=self.user, group=self.group,
                    url=self.request.route_url(
                        'group-details', id=self.group.id))

            elif action == 'downgrade':
                if membership.get_role() == MembershipRole.USER:
                    membership.status = MembershipStatus.UNAPPROVED
                    msg = _(u'User %s is no longer in the group %s' % (
                        self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.REMOVED_GROUP_MEMBERSHIP,
                        self.group.name)
                elif membership.get_role() == MembershipRole.EDITOR:
                    membership.role = MembershipRole.USER
                    msg = _(u'User %s is now USER of the group '
                        '%s' % (self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.DOWNGRADED_GROUP_MEMBERSHIP,
                        'USER: %s' % self.group.name)
                elif membership.get_role() == MembershipRole.SPONSOR:
                    membership.role = MembershipRole.EDITOR
                    msg = _(u'User %s is now EDITOR of the group %s' % (
                        self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.DOWNGRADED_GROUP_MEMBERSHIP,
                        'EDITOR: %s' % self.group.name)
                elif membership.get_role() == MembershipRole.ADMINISTRATOR:
                    membership.role = MembershipRole.SPONSOR
                    msg = _(u'User %s is now SPONSOR of the group %s' % (
                        self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.DOWNGRADED_GROUP_MEMBERSHIP,
                        'SPONSOR: %s' % self.group.name)
                email.set_msg(
                    topic='downgrade',
                    people=self.user, group=self.group, role=membership.role)

            elif action == 'revoke':
                log_type = AccountLogType.REVOKED_GROUP_MEMBERSHIP_BY_ADMIN
                membership.status = MembershipStatus.UNAPPROVED
                membership.role = MembershipRole.USER
                msg = _(u'User %s is no longer in the group %s' % (
                    self.user.username, self.group.name))
                register.save_account_activity(
                    self.request,
                    self.user.id,
                    log_type,
                    self.group.name)
                email.set_msg(
                    topic='revoke',
                    body='body_admin_revoked',
                    people=self.user, group=self.group, reason=reason)

            elif action == 'change_admin':
                form = GroupAdminsForm(self.request.POST, self.group)
                form.owner_id.choices = [
                    (m.people.id, m.people.username)
                    for m in self.group.members
                    if m.role == MembershipRole.ADMINISTRATOR]
                if form.validate():
                    form.populate_obj(self.group)
                    log_type = AccountLogType.CHANGED_GROUP_MAIN_ADMIN
                    msg = _(u'You are no longer the principal administrator')
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        log_type,
                        self.group.name)

            if msg:
                self.request.session.flash(msg, 'info')

            if email.is_ready:
                email.send(self.user.email)

        return redirect_to('/group/details/%s' % self.group.id)
