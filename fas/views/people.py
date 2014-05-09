# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPBadRequest

from fas.models import DBSession

import fas.models.provider as provider


@view_config(route_name='people')
def index(request):
    """ People list landing page. """
    return HTTPFound(location='/people/page/1')


@view_config(route_name='people-paging', renderer='/people/list.xhtml')
def paging(request):
    """ People list's view with paging. """
    try:
        page = int(request.matchdict['pagenb'])
    except KeyError:
        page = 1
    count = provider.get_people_count(DBSession)[0]
    #TODO: get limit from config file
    people = provider.get_people(DBSession, 50, page)
    pages = count / 50
    print 'request page %i' % page
    return dict(
        request=request,
        people=people,
        people_count=count,
        page=page,
        pages=pages
        )

@view_config(route_name='people-profile', renderer='/people/profile.xhtml')
def profile(request):
    """ People profile page. """
    try:
        id = request.matchdict['id']
    except KeyError:
        return HTTPBadRequest()

    person = provider.get_people_by_id(DBSession, id)

    return dict(person=person, membership=person.group_membership)