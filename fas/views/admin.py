# -*- coding: utf-8 -*-

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED

import fas.models.provider as provider

from fas.views import redirect_to
from fas.utils import Config


class Admin(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='admin', permission='admin')
    def index(self):
        """ Admin panel page."""
        return Response('This is an empty page')