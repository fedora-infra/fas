# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest

import fas.models.provider as provider

from fas.views import redirect_to

from fas.utils import compute_list_pages_from

from fas.security import ParamsValidator


@view_config(route_name="groups")
def index(request):
    """ Groups list landing page. """
    return redirect_to('/groups/page/1')


@view_config(route_name='groups-paging', renderer='/groups/list.xhtml')
def paging(request):
    """ Groups' list view with paging feature. """
    try:
        page = int(request.matchdict.get('pagenb', 1))
    except ValueError:
        return HTTPBadRequest()

    #TODO: still, get limit from config file or let user choose in between
    #TODO: predifined one?
    groups = provider.get_groups(50, page)

    pages, count = compute_list_pages_from('groups', 50)

    if page > pages:
        return HTTPBadRequest()

    return dict(
        request=request,
        groups=groups,
        count=count,
        page=page,
        pages=pages
        )


@view_config(route_name='group-details', renderer='/groups/details.xhtml')
def details(request):
    """ Group's details page."""
    try:
        id = request.matchdict['id']
    except KeyError:
        return HTTPBadRequest()

    limit = 50

    params = ParamsValidator(request)
    params.add_optional('members')
    params.add_optional('members_page')

    membership = provider.get_group_membership(id)

    group = membership[0][0]
    members = []
    people = []

    for group, member, person, roles in membership:
        members.append(member)
        people.append((person, roles))

    # Disable paging for now
    #obj_start = 0
    #obj_max = limit
    page = 1
    #if params.is_valid():
        #page = int(params.get_optional('members_page')) or 1
        #if page > 1:
            #obj_max = (limit * page)
            #obj_start = (obj_max - limit) + 1
        #else:
            #obj_max = limit
            #obj_start = 0

    return dict(
        group=group,
        members=people,
        count=len(people),
        page=page,
        pages=int(len(people) / limit)
        )