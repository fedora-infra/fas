# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou All rights reserved.
# Copyright © 2008 Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
#            Yaakov Nemoy <ynemoy@redhat.com>
#
import turbogears
from turbogears import controllers, expose, paginate, \
                       identity, redirect, widgets, validate, \
                       validators, error_handler
from turbogears.database import session, metadata, mapper

import cherrypy
import re

from sqlalchemy import Table, Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relation, backref
from sqlalchemy.exceptions import IntegrityError, InvalidRequestError

from genshi.template.plugin import TextTemplateEnginePlugin

import fas.sidebar as sidebar
import logging
import fas.plugin as plugin
from fas.auth import can_view_group

from fas.model.fasmodel import Groups, GroupsTable, People

from fas_show.help import Help

shows_table = Table('show_shows', metadata,
                    Column('id', Integer,
                           autoincrement=True,
                           primary_key=True),
                    Column('name', Text),
                    Column('description', Text),
                    Column('owner_id', Integer,
                           ForeignKey('people.id')),
                    Column('group_id', Integer,
                           ForeignKey('groups.id')),
                    Column('long_name', Text))

user_signups_table = \
    Table('show_user_signups', metadata,
          Column('id', Integer,
                 autoincrement=True,
                 primary_key=True),
          Column('show_id', Integer,
                 ForeignKey('show_shows.id')),
          Column('people_id', Integer,
                 ForeignKey('people.id'),
                 unique=True))


class Show(object):
    @classmethod
    def by_name(cls, name):
        return cls.query.filter_by(name=name).one()
    pass


mapper(Show, shows_table,
       properties= \
        dict(group=relation(Groups, uselist=False, backref='show'),
             owner=relation(People, backref='shows'),
             user_signups=relation(People, 
                                   backref=backref('show', uselist=False),
                                   secondary=user_signups_table)))

class ShowPlugin(controllers.Controller):
    capabilities = ['show_plugin']

    def __init__(self):
        '''Create a Show Controller.'''
        self.path = ''
        
    help = Help()
    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @expose(template="fas_show.templates.index")
    @error_handler(error) # pylint: disable-msg=E0602
    def index(self):
        turbogears.redirect('/show/list')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="genshi-text:fas_show.templates.list",
            as_format="plain", accept_format="text/plain",
            format="text", content_type='text/plain; charset=utf-8')
    @expose(template="fas_show.templates.list", allow_json=True)
    @error_handler(error) # pylint: disable-msg=E0602
    def list(self, search='*'):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        re_search = re.sub(r'\*', r'%', search).lower()
        results = Show.query.filter(Show.name.like(re_search)).order_by('name').all()
        shows = list()
        for show in results:
            if can_view_group(person, show.group):
                shows.append(show)
        if not len(shows):
            turbogears.flash(_("No Shows found matching '%s'") % search)
        return dict(shows=shows, search=search)

    @identity.require(turbogears.identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas_show.templates.view", allow_json=True)
    def view(self, show):
        '''View Show'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        show = Show.by_name(show)

        if not can_view_group(person, show.group):
            turbogears.flash(_("You cannot view '%s'") % show.name)
            turbogears.redirect('/show/list')
            return dict()
        return dict(show=show)
    
    @identity.require(turbogears.identity.not_anonymous())
    @expose(template='fas_show.templates.new')
    @error_handler(error) # pylint: disable-msg=E0602
    def new(self):
        return dict()
    
    @identity.require(turbogears.identity.not_anonymous())
    @expose()
    @error_handler(error) # pylint: disable-msg=E0602
    def create(self, name, display_name, owner, group, description):
        show = Show()
        show.name = name
        show.long_name = display_name
        show.description = description
        owner = People.by_username(owner)
        show.owner = owner
        group = Groups.by_name(group)
        show.group = group
        session.flush()
        turbogears.redirect('/show/view/%s' % name)
        return dict()
    
    @identity.require(turbogears.identity.not_anonymous())
    @expose(template='fas_show.templates.edit')
    @error_handler(error) # pylint: disable-msg=E0602
    def edit(self, show):
        show = Show.by_name(show)
        return dict(show=show)
    
    @identity.require(turbogears.identity.not_anonymous())
    @expose()
    @error_handler(error) # pylint: disable-msg=E0602
    def save(self, name, display_name, owner, group, description):
        show = Show.by_name(name)
        show.name = name
        show.long_name = display_name
        show.description = description
        owner = People.by_username(owner)
        show.owner = owner
        group = Groups.by_name(group)
        show.group = group
        session.flush()
        turbogears.redirect('/show/view/%s' % name)

    @expose(template="fas_show.templates.join")
    @error_handler(error) # pylint: disable-msg=E0602
    def join(self, show=None):
        if not show:
            turbogears.redirect('/show/list/')
        if identity.not_anonymous():
            identity.current.logout()
        show = Show.by_name(show)
        return dict(show=show)

    @expose()
    @error_handler(error) # pylint: disable-msg=E0602
    def add_user(self, show, username, human_name, email, telephone=None, 
               postal_address=None, age_check=False):
        if identity.not_anonymous():
            identity.current.logout()
        try:
            user = \
                self._root.user.create_user(username, human_name, email, 
                                            telephone, postal_address, 
                                            age_check, 
                                            redirect='/show/join/%s' % show)
            
            show = Show.by_name(show)
            user.show = show
        except IntegrityError:
            turbogears.flash(_("Your account could not be created.  Please contact a Fedora Ambassador for assistance."))
            turbogears.redirect('/show/fail/%s' % show)
            return dict()
        else:
            turbogears.flash(_('Your password has been emailed to you.  Please log in with it and change your password'))
            turbogears.redirect('/show/success/%s' % show)

        turbogears.redirect('/show/join/%s' % show)
    
    @expose(template='fas_show.templates.success')
    @error_handler(error) # pylint: disable-msg=E0602
    def success(self, show):
        return dict(show=show)
    
    @expose(template='fas_show.templates.fail')
    @error_handler(error) # pylint: disable-msg=E0602
    def fail(self, show):
        return dict(show=show)

    @classmethod
    def initPlugin(cls, controller):
        cls.log = logging.getLogger('plugin.show')
        cls.log.info('Show plugin initializing')
        try:
            path, self = controller.requestpath(cls, '/show')
            cls.log.info('Show plugin hooked')
            self.path = path
            if self.sidebarentries not in sidebar.entryfuncs:
                sidebar.entryfuncs.append(self.sidebarentries)
        except (plugin.BadPathException,
            plugin.PathUnavailableException), e:
            cls.log.info('Show plugin hook failure: %s' % e)

    def delPlugin(self, controller):
        self.log.info('Show plugin shutting down')
        if self.sidebarentries in sidebar.entryfuncs:
            sidebar.entryfuncs.remove(self.sidebarentries)
            
    def sidebarentries(self):
        return [('Shows and Events', self.path)]
