# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from fas.models import DBSession

import fas.models.provider as provider


@view_config(route_name='people')
def index(request):
    """ People list landing page. """
    return HTTPFound(location='/people/page/1')


@view_config(route_name='people-paging', renderer='/people.xhtml')
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


def profile(request):
    pass