# -*- coding: utf-8 -*-
import turbogears
from turbogears import controllers, expose, paginate, \
                       identity, redirect, widgets, validate, \
                       validators, error_handler
from turbogears.database import session, metadata, mapper

import cherrypy

from sqlalchemy import Table, Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relation, backref

from genshi.template.plugin import TextTemplateEnginePlugin

import fas.sidebar as sidebar
import logging
import fas.plugin as plugin

from fas.model.fasmodel import Groups, GroupsTable

shows_table = Table('show_shows', metadata,
                    Column('id', Integer,
                           autoincrement=True,
                           primary_key=True),
                    Column('name', Text),
                    Column('owner', Text),
                    Column('group_id', Integer,
                           ForeignKey('groups.id')),
                    Column('long_name', Text))

class Show(object):
    pass

mapper(Show, shows_table,
       properties= \
        dict(group=relation(Groups, uselist=False, backref='show')))

class ShowPlugin(controllers.Controller):
    capabilities = ['show_plugin']

    def __init__(self):
        '''Create a Show Controller.'''
        self.path = ''

    @expose(template="fas_show.templates.index")
    def index(self):
        value = "my Val"
        return dict(value=value)

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
            turbogears.flash(_("No Groups found matching '%s'") % search)
        return dict(shows=results, search=search)
    #, memberships=memberships)


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
