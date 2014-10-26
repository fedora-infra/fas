# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED

from fas.models import MembershipStatus

import fas.models.provider as provider

from fas.views import redirect_to
from fas.utils import compute_list_pages_from

from fas.forms.people import ContactInfosForm
from fas.forms.la import SignLicenseForm
from fas.forms.group import EditGroupForm

from fas.security import MembershipValidator
from fas.security import ParamsValidator

from fas.utils.fgithub import Github
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
                'No group found for the query: %s' % _id, 'error')
            return redirect_to('/groups')

        pages, count = compute_list_pages_from(groups_cnt, 50)

        if page > pages:
            return HTTPBadRequest()

        if grpname and len(groups) == 1 and page == 1:
            self.request.session.flash(
                "Only one group matching, redirecting to the group's page",
                'info')
            return redirect_to('/group/deails/%s' % groups[0].id)

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

        g_memberships = provider.get_group_membership(_id)

        group = g_memberships[0][0]
        memberships = []
        members = []

        authenticated = self.request.get_user
        authenticated_membership = None
        is_member = False

        for group, membership, member in g_memberships:
            memberships.append(membership)
            if authenticated != member and\
            membership.status == MembershipStatus.APPROVED:
                members.append((member, membership.get_role()))
            else:
                authenticated = member
                authenticated_membership = membership
                if membership.get_status() == MembershipStatus.APPROVED:
                    is_member = True

        membership_requets = provider.get_memberships_by_status(
            status=MembershipStatus.PENDING,
            group=group.id
            )

        license_signed_up = None
        if self.request.authenticated_userid:
            license_signed_up = provider.is_license_signed(
                group.license_sign_up, self.request.get_user.id)

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
            count=len(members),
            license_signed_up=license_signed_up,
            page=page,
            pages=int(len(members) / limit),
            person=authenticated,
            person_membership=authenticated_membership,
            is_member=is_member,
            membership_status=MembershipStatus,
            membership_request=membership_requets,
            userform=user_form,
            licenseform=license_form,
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
