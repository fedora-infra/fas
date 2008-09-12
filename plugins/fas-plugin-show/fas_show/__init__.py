# -*- coding: utf-8 -*-
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
from fas.auth import canViewGroup

from fas.model.fasmodel import Groups, GroupsTable, People

shows_table = Table('show_shows', metadata,
                    Column('id', Integer,
                           autoincrement=True,
                           primary_key=True),
                    Column('name', Text),
                    Column('owner_id', Integer,
                           ForeignKey('people.id')),
                    Column('group_id', Integer,
                           ForeignKey('groups.id')),
                    Column('long_name', Text))

class Show(object):
    @classmethod
    def by_name(cls, name):
        return cls.query.filter_by(name=name).one()
    pass

mapper(Show, shows_table,
       properties= \
        dict(group=relation(Groups, uselist=False, backref='show'),
             owner=relation(People, backref='shows')))

class ShowPlugin(controllers.Controller):
    capabilities = ['show_plugin']

    def __init__(self):
        '''Create a Show Controller.'''
        self.path = ''

    @expose(template="fas_show.templates.index")
    def index(self):
        turbogears.redirect('/show/list')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="genshi-text:fas_show.templates.list",
            as_format="plain", accept_format="text/plain",
            format="text", content_type='text/plain; charset=utf-8')
    @expose(template="fas_show.templates.list", allow_json=True)
    def list(self, search='*'):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

#        memberships = {}
#        groups = []
        re_search = re.sub(r'\*', r'%', search).lower()
        results = Show.query.filter(Show.name.like(re_search)).order_by('name').all()
# This code has been airlifted from groups
# retained if we need this sort of logic in the future
#        if self.jsonRequest():
#            membersql = sqlalchemy.select([PersonRoles.c.person_id, PersonRoles.c.group_id, PersonRoles.c.role_type], PersonRoles.c.role_status=='approved').order_by(PersonRoles.c.group_id)
#            members = membersql.execute()
#            for member in members:
#                try:
#                    memberships[member[1]].append({'person_id': member[0], 'role_type': member[2]})
#                except KeyError:
#                    memberships[member[1]]=[{'person_id': member[0], 'role_type': member[2]}]
#        for group in results:
#            if canViewGroup(person, group):
#                groups.append(group)
        if not len(results):
            turbogears.flash(_("No Shows found matching '%s'") % search)
        return dict(shows=results, search=search)
    #, memberships=memberships)

    @identity.require(turbogears.identity.not_anonymous())
#    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas_show.templates.view", allow_json=True)
    def view(self, show):
        '''View Show'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        show = Show.by_name(show)

        if not canViewGroup(person, show.group):
            turbogears.flash(_("You cannot view '%s'") % show.name)
            turbogears.redirect('/show/list')
            return dict()

        # Also return information on who is not sponsored
#        unsponsored = PersonRoles.query.join('group').filter(and_(
#            PersonRoles.role_status=='unapproved', Groups.name==show.group.name))
#        unsponsored.json_props = {'PersonRoles': ['member']}
        
        return dict(show=show)
    
    @expose(template="fas_show.templates.join")
    def join(self, show=None):
        if not show:
            turbogears.redirect('/show/list/')
        if identity.not_anonymous():
            identity.current.logout()
        show = Show.by_name(show)
        return dict(show=show)

    @expose()
    def add_user(self, show, username, human_name, email, telephone=None, 
               postal_address=None, age_check=False):
        if identity.not_anonymous():
            identity.current.logout()
        try:
            self._root.user.create_user(username, human_name, email, 
                                        telephone, postal_address, 
                                        age_check, 
                                        redirect='/show/join/%s' % show)
        except IntegrityError:
            turbogears.flash(_("Your account could not be created.  Please contact a Fedora Ambassador for assistance."))
            turbogears.redirect('/show/fail/%s' % show)
            return dict()
        else:
            turbogears.flash(_('Your password has been emailed to you.  Please log in with it and change your password'))
            turbogears.redirect('/show/success/%s' % show)

        turbogears.redirect('/show/join/%s' % show)
    
    @expose(template='fas_show.templates.success')
    def success(self, show):
        return dict(show=show)
    
    @expose(template='fas_show.templates.fail')
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
        return [('Show plugin', self.path)]
