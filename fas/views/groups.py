# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPBadRequest

from fas.models import DBSession
from fas.models.people import People
from fas.models.group import Groups
from fas.models.group import GroupMembership
from fas.models import RoleLevel

from math import ceil

import fas.models.provider as provider


@view_config(route_name="groups")
def index(request):
    """ Groups list landing page. """
    return HTTPFound(location='/groups/page/1')


@view_config(route_name='groups-paging', renderer='/groups/list.xhtml')
def paging(request):
    """ Groups' list view with paging feature. """
    try:
        page = int(request.matchdict.get('pagenb', 1))
    except ValueError:
        return HTTPBadRequest()

    count = provider.get_groups_count(DBSession)[0]
    #TODO: still, get limit from config file
    groups = provider.get_groups(DBSession, 50, page)
    pages = ceil(float(count) / float(50))

    return dict(
        request=request,
        groups=groups,
        groups_count=count,
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

    membership = provider.get_group_membership(DBSession, id)

    group = membership[0][0]
    members = []
    people = []

    for obj in membership:
        members.append(obj[1])
        people.append((obj[2], obj[3]))

    return dict(group=group, members=people)