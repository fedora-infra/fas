# -*- coding: utf-8 -*-
import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import cherrypy

from genshi.template.plugin import TextTemplateEnginePlugin

import fas.sidebar as sidebar
import logging
import fas.plugin as plugin

from fas.model import People, PeopleTable, PersonRolesTable, GroupsTable, Configs
from fas.model import Log

from fas.auth import *
from fas.user import KnownUser
from fas.util import available_languages

class AsteriskSave(validators.Schema):
    targetname = KnownUser
    asterisk_enabled = validators.OneOf(['0', '1'], not_empty=True)
    asterisk_pass = validators.String(min=6, not_empty=True)

def get_configs(configs_list):
    configs = {}
    for config in configs_list:
        configs[config.attribute] = config.value
    if 'enabled' not in configs:
        configs['enabled'] = '0'
    if 'pass' not in configs:
        configs['pass'] = 'Not Defined'
    return configs

class AsteriskPlugin(controllers.Controller):
    capabilities = ['asterisk_plugin']

    def __init__(self):
        '''Create Asterisk Controller.'''
        self.path = ''
    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas_asterisk.templates.index")
    def index(self):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if turbogears.identity.current.user_name == username:
            personal = True
        else:
            personal = False
        # TODO: We can do this without a db lookup by using something like
        # if groupname in identity.groups: pass
        # We may want to do that in isAdmin() though. -Toshio
        user = People.by_username(turbogears.identity.current.user_name)
        if isAdmin(user):
            admin = True
        else:
            admin = False
        if turbogears.identity.current.user_name == username:
            personal = True
        else:
            personal = False

        configs = get_configs(Configs.query.filter_by(person_id=person.id, application='asterisk').all())
        return dict(admin=admin, person=person, personal=personal, configs=configs)

    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)


    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas_asterisk.templates.edit")
    def edit(self, targetname=None):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)

        admin = isAdmin(person)
        configs = get_configs(Configs.query.filter_by(person_id=target.id, application='asterisk').all())
        return dict(admin=admin, person=person, configs=configs,target=target)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=AsteriskSave())
    @error_handler(error)
    @expose(template='fas_asterisk.templates.edit')
    def save(self, targetname, asterisk_enabled, asterisk_pass):
        person = People.by_username(turbogears.identity.current.user_name)
        target = People.by_username(targetname)
        
        if not canEditUser(person, target):
            turbogears.flash(_("You do not have permission to edit '%s'") % target.username)
            turbogears.redirect('/user/view/%s', target.username)
            return dict()

        
        cur_configs = Configs.query.filter_by(person_id=target.id, application='asterisk').all()
        if len(cur_configs) == 0:
            configs = Configs(application='asterisk', attribute='pass', value=asterisk_pass)
            target.configs.append(configs)
            print asterisk_enabled
            configs = Configs(application='asterisk', attribute='enabled', value=asterisk_enabled)
            target.configs.append(configs)
        else:
            for config in cur_configs:
                if config.attribute == 'pass':
                    config.value = asterisk_pass
                elif config.attribute == 'enabled':
                    config.value = asterisk_enabled
        turbogears.redirect("/asterisk/")
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(format="json", allow_json=True)
    def dump(self):
        asterisk_attrs = {}
        for attr in Configs.query.filter_by(application='asterisk').all():
            if attr.person_id not in asterisk_attrs:
                asterisk_attrs[attr.person_id] = {}
            asterisk_attrs[attr.person_id][attr.attribute] = attr.value
        return dict(asterisk_attrs=asterisk_attrs)
    
    @classmethod
    def initPlugin(cls, controller):
        cls.log = logging.getLogger('plugin.asterisk')
        cls.log.info('Asterisk plugin initializing')
        try:
            path, self = controller.requestpath(cls, '/asterisk')
            cls.log.info('Asterisk plugin hooked')
            self.path = path
            if self.sidebarentries not in sidebar.entryfuncs:
                sidebar.entryfuncs.append(self.sidebarentries)
        except (plugin.BadPathException,
            plugin.PathUnavailableException), e:
            cls.log.info('Asterisk plugin hook failure: %s' % e)

    def delPlugin(self, controller):
        self.log.info('Asterisk plugin shutting down')
        if self.sidebarentries in sidebar.entryfuncs:
            sidebar.entryfuncs.remove(self.sidebarentries)

    def sidebarentries(self):
        return [('VoIP', self.path)]
