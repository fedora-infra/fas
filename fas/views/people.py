# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED

import fas.models.provider as provider

from fas.views import redirect_to
from fas.utils import compute_list_pages_from


class People(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='people')
    def index(self):
        """ People list landing page. """
        return redirect_to('/people/page/1')

    @view_config(route_name='people-paging', renderer='/people/list.xhtml',
        permission=NO_PERMISSION_REQUIRED)
    def paging(self):
        """ People list's view with paging. """
        try:
            page = int(self.request.matchdict.get('pagenb', 1))
        except ValueError:
            return HTTPBadRequest()

        #TODO: get limit from config file or let user choose in between
        #      predefined one ?
        people = provider.get_people(50, page)

        pages, count = compute_list_pages_from('people', 50)

        if page > pages:
            return HTTPBadRequest()

        return dict(
            people=people,
            count=count,
            page=page,
            pages=pages
            )

    @view_config(route_name='people-profile', renderer='/people/profile.xhtml')
    def profile(self):
        """ People profile page. """
        try:
            _id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        person = provider.get_people_by_id(_id)

        return dict(person=person, membership=person.group_membership)

    @view_config(route_name='people-activities',
        renderer='/people/activities.xhtml')
    def activities(self):
        """ People's activities page. """
        try:
            _id = self.request.matchdict['id']
        except KeyError:
            return HTTPBadRequest()

        activities = provider.get_account_activities_by_people_id(_id)

        # Prevent client/user from requesting direct url
        if len(activities) == 0:
            return redirect_to('/people/profile/%s' % _id)

        return dict(activities=activities, person=activities[0].person)

    @view_config(route_name='people-edit', permission='owner')
    def edit(self):
        """ Profile's edit page."""
        return Response('This is an empty edit page.')