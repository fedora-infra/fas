# -*- coding: utf-8 -*-

from pyramid.events import subscriber

from fas.events import GroupBindingRequested

from fas.utils import _
from fas.utils.fgithub import Github

import logging

log = logging.getLogger(__name__)


@subscriber(GroupBindingRequested)
def create_gh_team(event):
    """ Create a github team base on group name."""
    group = str(event.form.name.data)
    gh = Github(logger=log)

    if not gh.create_group(name=group, repo=group, access='push'):
        event.form.bound_to_github.data = False
        event.form.populate_obj(event.group)
        event.request.session.flash(
            _(u'Your group cannot be bound to our GitHub organisation\n'
            'If you keep having this issue please, contact an admin'),
            'error')
    else:
        event.request.session.flash(
            _(u'Group successfully bound to github'), 'info')
