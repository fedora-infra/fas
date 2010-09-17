# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect, validate
import tw.forms.validators as validators
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController
from repoze.what import predicates

from fas.lib.base import BaseController
from fas.model import DBSession, metadata
from fas.controllers.error import ErrorController
from fas import model
from fas.controllers.secure import SecureController

from ipalib import api

api.bootstrap(debug=False)
api.finalize()

class GroupList(validators.Schema):
    search = validators.UnicodeString(max=32)

class Group(BaseController):
    """
        Group Controller for group listing and operations
    """

    @validate(validators=GroupList())
    @expose('fas.templates.group.list')
    def list(self, search=u'a'):
        """Return a simple group list"""
        api.Backend.xmlclient.connect()
        groups = api.Command.group_find(search)
        api.Backend.xmlclient.disconnect()
        return dict(groups=groups, search=search)

