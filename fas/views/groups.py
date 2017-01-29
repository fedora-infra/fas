# -*- coding: utf-8 -*-
#
# Copyright © 2014-2016 Xavier Lamien.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# __author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

import datetime
import logging
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.security import NO_PERMISSION_REQUIRED
import mistune
from fas.models.people import AccountStatus, AccountLogType
from fas.models.group import GroupStatus, MembershipStatus, MembershipRole
from fas.views import redirect_to
from fas.util import compute_list_pages_from, setup_group_form
from fas.forms.people import ContactInfosForm, PeopleForm
from fas.forms.la import SignLicenseForm
from fas.forms.group import GroupAdminsForm
from fas.forms.certificates import CreateClientCertificateForm
from fas.security import MembershipValidator
from fas.security import ParamsValidator
from fas.util import _, Config
from fas.events import GroupBindingRequested, NotificationRequest
from fas.events import GroupEdited
import fas.models.provider as provider
import fas.models.register as register

log = logging.getLogger(__name__)


class Groups(object):
    def __init__(self, request):
        self.request = request
        self.notify = self.request.registry.notify
        self.params = ParamsValidator(request)
        self.group = None
        self.id = -1

    @view_config(route_name="groups", renderer='/groups/list.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    @view_config(route_name='groups-paging', renderer='/groups/list.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    def paging(self):
        """ Groups' list view with paging feature. """
        try:
            page = int(self.request.matchdict.get('pagenb', 1))
        except ValueError:
            return HTTPBadRequest('The page provided is invalid')

        # TODO: still, get limit from config file or let user choose in between
        # TODO: predifined one?
        groups = provider.get_groups(50, page)
        groups_cnt = provider.get_groups(count=True)

        pages = compute_list_pages_from(groups_cnt, 50)

        if page > pages or page < 1:
            return HTTPBadRequest(
                'The page is outside the valid number of pages')

        return dict(
            groups=groups,
            count=int(groups_cnt),
            page=page,
            pages=pages
        )

    @view_config(route_name='group-search-rd')
    def search_redirect(self):
        """ Redirect the search to the proper url. """
        query = self.request.params.get('q', '*')
        return redirect_to(self.request, 'group-search', pattern=query)

    @view_config(route_name='group-search', renderer='/groups/list.xhtml')
    @view_config(route_name='group-search-paging', renderer='/groups/list.xhtml')
    def search(self):
        """ Search groups. """
        try:
            _id = self.request.matchdict['pattern']
        except KeyError:
            return HTTPBadRequest('No pattern specified')
        page = int(self.request.matchdict.get('pagenb', 1))

        grpname = None
        try:
            _id = int(_id)
        except ValueError:
            grpname = _id

        if grpname:
            if '*' in grpname:
                grpname = grpname.replace('*', '%')
            else:
                grpname += '%'
            groups = provider.get_groups(50, page, pattern=grpname)
            groups_cnt = provider.get_groups(
                pattern=grpname, count=True)
        else:
            groups = provider.get_group_by_id(_id)
            groups_cnt = 1

        if not groups:
            self.request.session.flash(
                _(u'No group found for the query %s ' % _id), 'error')
            return redirect_to(self.request, 'groups')

        pages = compute_list_pages_from(groups_cnt, 50)

        if page > pages:
            return HTTPBadRequest(
                'The page is bigger than the maximum number of pages')

        if grpname and len(groups) == 1 and page == 1:
            self.request.session.flash(
                _("Only one group matching, redirecting to the group's page"),
                'info')
            return redirect_to(self.request, 'group-details', id=groups[0].id)

        return dict(
            groups=groups,
            page=page,
            pages=pages,
            count=int(groups_cnt),
            pattern=_id
        )

    @view_config(route_name='group-details', renderer='/groups/details.xhtml',
                 permission=NO_PERMISSION_REQUIRED)
    def details(self):
        """ Group's details page. """
        try:
            _id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest('No id specified')

        limit = 50

        self.params.add_optional('members')
        self.params.add_optional('members_page')

        user_form = ContactInfosForm(self.request.POST, self.request.get_user)
        license_form = SignLicenseForm(self.request.POST)
        people_form = PeopleForm(self.request.POST)
        cert_form = CreateClientCertificateForm(self.request.POST)

        if _id.isdigit():
            group = provider.get_group_by_id(_id)
        else:
            group = provider.get_group_by_name(_id)

        if not group:
            return HTTPNotFound('No group found with identifier: %s' % _id)

        g_memberships = provider.get_group_membership(group.id)

        memberships = []
        members = []
        user_members = []
        sponsor_members = []
        admin_members = []
        admin_form = None
        valid_active_status = [
            AccountStatus.ACTIVE,
            AccountStatus.INACTIVE,
            AccountStatus.ON_VACATION]

        if not self.request.authenticated_is_admin():
            if group.status not in [
                GroupStatus.ACTIVE,
                GroupStatus.INACTIVE
            ]:
                return redirect_to(self.request, 'groups')

        authenticated = self.request.get_user
        authenticated_membership = None
        is_member = False

        for grp, membership, member in g_memberships:
            memberships.append(membership)
            if authenticated == member:
                authenticated_membership = membership
            if membership.status == MembershipStatus.APPROVED \
                    and member.status in valid_active_status:
                if membership.role == MembershipRole.USER:
                    user_members.append(membership)
                elif membership.role == MembershipRole.SPONSOR \
                        and grp.requires_sponsorship:
                    sponsor_members.append(membership)
                elif membership.role == MembershipRole.ADMINISTRATOR:
                    admin_members.append(membership)
                if authenticated == member:
                    is_member = True
                members.append(membership)

        if authenticated:
            if authenticated.id == group.owner_id \
                    or self.request.authenticated_is_admin():
                admin_form = GroupAdminsForm(self.request.POST)
                admin_form.owner_id.choices = [
                    (p.person.id, '%s (%s)'
                     % (p.person.username, p.person.fullname))
                    for p in admin_members]

        membership_request = provider.get_memberships_by_status(
            status=MembershipStatus.PENDING,
            group=[group.id]
        )

        license_signed_up = None
        if self.request.authenticated_userid and self.request.get_user.licenses:
            license_signed_up = provider.is_license_signed(
                self.request.get_user.id, group.id)

        # Assign some data we expect
        cert_form.cacert.data = group.certificate_id
        cert_form.group_id.data = group.id
        cert_form.group_name.data = group.name

        # FIXME: filter out members from people list.
        # people_form.people.choices = [
        # (u.id, u.username + ' (' + u.fullname + ')')
        # for u in provider.get_people()]

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
            formcertificate=cert_form,
            text=mistune,
            group_status=GroupStatus,
        )

    @view_config(route_name='group-edit', permission='authenticated',
                 renderer='/groups/edit.xhtml')
    def edit(self):
        """ group editor page."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest('No id specified')

        self.group = provider.get_group_by_id(self.id)

        ms = MembershipValidator(self.request.authenticated_userid,
                                 [self.group.name])
        # TODO: move this to Auth provider?
        # Prevent denied client from requesting direct url
        if not self.request.authenticated_is_admin():
            if not self.request.authenticated_is_modo():
                if not self.request.authenticated_is_group_admin(
                        self.group.name):
                    return redirect_to(self.request, 'group-details', id=self.id)

        form = setup_group_form(self.request, self.group)

        if self.request.method == 'POST' \
                and ('form.save.group-details' in self.request.params):
            if form.validate():
                self.notify(GroupEdited(
                    self.request,
                    person=self.request.get_user,
                    group=self.group,
                    form=form))

                # The following keys are using foreign keys for which
                # the referenced key might not exist. We need to set them
                # to Null to avoid to trigger a relationship against
                # a non-existing key -1 or 0.
                if form.parent_group_id.data <= 0:
                    form.parent_group_id.data = None
                if form.license_id.data <= 0:
                    form.license_id.data = None
                if form.certificate_id.data <= 0:
                    form.certificate_id.data = None

                if form.bound_to_github.data \
                        and self.group.bound_to_github is False:
                    self.notify(
                        GroupBindingRequested(self.request, form, self.group))
                else:
                    form.populate_obj(self.group)

                return redirect_to(self.request, 'group-details', id=self.id)

        return dict(form=form, id=self.id)

    @view_config(route_name='group-apply', permission='authenticated')
    def group_apply(self):
        """ Apply to a group."""
        try:
            self.id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest('No id specified')

        form = PeopleForm(self.request.POST)

        self.group = provider.get_group_by_id(self.id)
        user = self.request.get_user

        membership = provider.get_membership_by_username(
            user.username, self.group.name)

        tpl = 'membership_update'

        can_apply = False
        if not membership:
            can_apply = True

        if self.group.license_id > -1:
            if provider.is_license_signed(
                    self.group.license_id, user.id):
                status = MembershipStatus.UNAPPROVED
                can_apply = False

        if self.request.method == 'POST':
            status = MembershipStatus.PENDING
            log = AccountLogType.ASKED_GROUP_MEMBERSHIP
            topic = 'group.member.apply'

            if not self.group.need_approval:
                status = MembershipStatus.APPROVED
                log = AccountLogType.NEW_GROUP_MEMBERSHIP
                topic = 'group.join'

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

                self.notify(NotificationRequest(
                    request=self.request,
                    topic=topic,
                    people=user,
                    group=self.group,
                    url=self.request.route_url(
                        'group-details', id=self.group.id),
                    template=tpl
                ))
            else:
                if membership.status == MembershipStatus.APPROVED:
                    self.request.session.flash(
                        _("You are already a member of this group"), 'info')
                elif membership.status == MembershipStatus.PENDING:
                    self.request.session.flash(
                        _("Your membership application already is pending"),
                        'info')
                elif membership.status == MembershipStatus.UNAPPROVED:
                    self.request.session.flash(
                        _("Your membership application has been declined"),
                        'error')

        return redirect_to(self.request, 'group-details', id=self.group.id)

    @view_config(route_name='group-action', permission='authenticated')
    @view_config(route_name='group-action', permission='authenticated', xhr=True,
                 renderer='json')
    def group_action(self):
        """ Upgrade or downgrade an user in a group."""
        if self.request.method == 'POST':
            form = PeopleForm(self.request.POST)

            group_id = self.request.POST.get('group_id')
            user_id = self.request.POST.get('user_id')
            role_id = self.request.POST.get('role_id')
            reason = self.request.POST.get('msg_text')

            if form.validate():
                user_id = form.people.data

            self.group = provider.get_group_by_id(group_id)
            self.user = provider.get_people_by_id(user_id)

            if self.user is not None:
                membership = provider.get_membership_by_username(
                    self.user.username, self.group.name)

            status = "ok"
            msg = ''
            tpl = "membership_update"
            log_type = None
            topic = ''
            action = self.request.POST.get('action')

            if action == 'invite':
                invitee = self.request.POST.get('invitee')
                if invitee:
                    self.notify(NotificationRequest(
                        request=self.request,
                        topic='group.invite',
                        people=self.request.get_user,
                        group=self.group,
                        organisation=Config.get('project.organisation'),
                        url=self.request.route_url(
                            'group-details', id=self.group.id),
                        target_email=invitee,
                        template=tpl
                    ))
                    msg = _(u'Invitation sent!')

            elif action == 'add':
                if form.validate():
                    register.add_membership(
                        self.group.id,
                        self.user.id,
                        MembershipStatus.APPROVED)
                    self.notify(NotificationRequest(
                        self.request,
                        topic='group.join',
                        people=self.user,
                        group=self.group,
                        url=self.request.route_url(
                            'group-details', id=self.group.id),
                        template=tpl
                    ))
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
                self.notify(NotificationRequest(
                    request=self.request,
                    topic='group.member.revoke',
                    body='body_self_removal',
                    people=self.user,
                    group=self.group,
                    template=tpl)
                )
                msg = _(u'You are no longer a member of this group')

            elif action == 'upgrade':
                role_id = int(role_id)
                if membership.status == MembershipStatus.PENDING:
                    topic = 'group.member.approve'
                    membership.status = MembershipStatus.APPROVED.value
                    msg = _(u'User %s is now an approved member of %s' % (
                        self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.NEW_GROUP_MEMBERSHIP,
                        self.group.name)
                elif membership.get_role(role_id - 1) == MembershipRole.USER:
                    topic = 'group.member.role.' + action
                    membership.role = MembershipRole.EDITOR.value
                    msg = _(u'User %s is now EDITOR of the group '
                            '%s' % (self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.PROMOTED_GROUP_MEMBERSHIP,
                        'EDITOR: %s' % self.group.name)
                elif membership.get_role(role_id - 1) == MembershipRole.EDITOR:
                    topic = 'group.member.role.' + action
                    membership.role = MembershipRole.SPONSOR.value
                    msg = _(u'User %s is now SPONSOR of the group '
                            '%s' % (self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.PROMOTED_GROUP_MEMBERSHIP,
                        'SPONSOR: %s' % self.group.name)
                elif membership.get_role(role_id - 1) == MembershipRole.SPONSOR:
                    topic = 'group.member.role.' + action
                    membership.role = MembershipRole.ADMINISTRATOR.value
                    msg = _(u'User %s is now ADMINISTRATOR of the '
                            'group %s' % (self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.PROMOTED_GROUP_MEMBERSHIP,
                        'ADMINISTRATOR: %s' % self.group.name)

                self.notify(NotificationRequest(
                    request=self.request,
                    topic=topic,
                    people=self.user,
                    group=self.group,
                    sponsor=self.request.get_user,
                    role=MembershipRole(membership.role),
                    url=self.request.route_url(
                        'group-details', id=self.group.id),
                    template=tpl
                ))

            elif action == 'downgrade':
                role_id = int(role_id)
                if membership.get_role(role_id) == MembershipRole.USER:
                    membership.status = MembershipStatus.UNAPPROVED.value
                    msg = _(u'User %s is no longer in the group %s' % (
                        self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.REMOVED_GROUP_MEMBERSHIP,
                        self.group.name)
                elif membership.get_role(role_id) == MembershipRole.EDITOR:
                    membership.role = MembershipRole.USER.value
                    msg = _(u'User %s is now USER of the group '
                            '%s' % (self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.DOWNGRADED_GROUP_MEMBERSHIP,
                        'USER: %s' % self.group.name)
                elif membership.get_role(role_id) == MembershipRole.SPONSOR:
                    membership.role = MembershipRole.EDITOR.value
                    msg = _(u'User %s is now EDITOR of the group %s' % (
                        self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.DOWNGRADED_GROUP_MEMBERSHIP,
                        'EDITOR: %s' % self.group.name)
                elif membership.get_role(role_id) == MembershipRole.ADMINISTRATOR:
                    membership.role = MembershipRole.SPONSOR.value
                    msg = _(u'User %s is now SPONSOR of the group %s' % (
                        self.user.username, self.group.name))
                    register.save_account_activity(
                        self.request,
                        self.user.id,
                        AccountLogType.DOWNGRADED_GROUP_MEMBERSHIP,
                        'SPONSOR: %s' % self.group.name)
                self.notify(NotificationRequest(
                    request=self.request,
                    topic='group.member.role.downgrade',
                    people=self.user,
                    group=self.group,
                    role=MembershipRole(membership.role),
                    template=tpl
                ))

            elif action == 'revoke':
                log_type = AccountLogType.REVOKED_GROUP_MEMBERSHIP_BY_ADMIN
                membership.status = MembershipStatus.UNAPPROVED.value
                membership.role = MembershipRole.USER.value
                msg = _(u'User %s is no longer in the group %s' % (
                    self.user.username, self.group.name))
                status = "removed"
                register.save_account_activity(
                    self.request,
                    self.user.id,
                    log_type,
                    self.group.name)
                self.notify(NotificationRequest(
                    request=self.request,
                    topic='group.member.revoke',
                    body='body_admin_revoked',
                    people=self.user,
                    group=self.group,
                    reason=reason,
                    template=tpl
                ))

            elif action == 'change_admin':
                form = GroupAdminsForm(self.request.POST, self.group)
                form.owner_id.choices = [
                    (m.person.id, m.person.username)
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

            if self.request.is_xhr:  # We only use js that set this in header
                resp = {"status": status, "msg": "{0:s}".format(msg)}
                return resp

            if msg:
                self.request.session.flash(msg, 'info')

        return redirect_to(self.request, 'group-details', id=self.group.id)

    @view_config(route_name='group-pending-request',
                 permission='authenticated',
                 renderer='/groups/pending-requests.xhtml')
    def pending_request(self):
        """ Pending membership requests view. """

        return dict(ms_requests=self.request.get_pending_ms_requests)
