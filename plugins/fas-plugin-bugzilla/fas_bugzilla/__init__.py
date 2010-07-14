# -*- coding: utf-8 -*-
import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session
from fas.model import Session, People

import cherrypy

from genshi.template.plugin import TextTemplateEnginePlugin

import fas.sidebar as sidebar
from fas.auth import *
import logging
import fas.plugin as plugin
from fas.model import Configs

class BugzillaSave(validators.Schema):
    bugzilla_email = validators.Email(strip=True, max=128)

def get_configs(configs_list):
    configs = {}
    for config in configs_list:
        configs[config.attribute] = config.value
    return configs

class BugzillaPlugin(controllers.Controller):
    capabilities = ['bugzilla_plugin']

    def __init__(self):
        '''Create a Bugzilla Controller.'''
        self.path = ''

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas_bugzilla.templates.index")
    def index(self):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if turbogears.identity.current.user_name == username:
            personal = True
        else:
            personal = False
        user = People.by_username(turbogears.identity.current.user_name)
        if is_admin(user):
            admin = True
        else:
            admin = False
        if turbogears.identity.current.user_name == username:
            personal = True
        else:
            personal = False
        configs = get_configs(Configs.query.filter_by(person_id=person.id, application='bugzilla').all())
        
        if 'bugzilla_email' in configs:
            is_set = True
        else:
            is_set = False
        return dict(admin=admin, person=person, personal=personal, is_set=is_set, configs=configs)

    @classmethod
    def initPlugin(cls, controller):
        cls.log = logging.getLogger('plugin.bugzilla')
        cls.log.info('Bugzilla plugin initializing')
        try:
            path, self = controller.requestpath(cls, '/bugzilla')
            cls.log.info('Bugzilla plugin hooked')
            self.path = path
            if self.sidebarentries not in sidebar.entryfuncs:
                sidebar.entryfuncs.append(self.sidebarentries)
        except (plugin.BadPathException,
            plugin.PathUnavailableException), e:
            cls.log.info('Bugzilla plugin hook failure: %s' % e)

    def delPlugin(self, controller):
        self.log.info('Bugzilla plugin shutting down')
        if self.sidebarentries in sidebar.entryfuncs:
            sidebar.entryfuncs.remove(self.sidebarentries)
            
    def sidebarentries(self):
        return [('Bugzilla plugin', self.path)]

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas_bugzilla.templates.edit")
    def edit(self, targetname=None):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        admin = is_admin(person)
        configs = get_configs(Configs.query.filter_by(person_id=person.id, application='bugzilla').all())
        if 'bugzilla_email' in configs:
            email = configs['bugzilla_email']
        else:
            email = target.email
        return dict(admin=admin, person=person, email=email, target=target)


    @expose(template="fas.templates.help")
    def help(self, id='none'):
        help = { 'none' :               [_('Error'), _('<p>We could not find that help item</p>')],
                 'bugzilla_change' :    [_('Bugzilla'), _('<p>Bugzilla has a seperate authentication system.  If you wish to have a different bugzilla address from your FAS address, please set that up here.  Not doing so will cause permission issues.</p>')]
        }
        
        try:
            helpItem = help[id]
        except KeyError:
            return dict(title=_('Error'), helpItem=[_('Error'), _('<p>We could not find that help item</p>')])
        return dict(help=helpItem)
    
    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)
    
    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=BugzillaSave())
    @error_handler(error)
    @expose(template='fas_bugzilla.templates.edit')
    def save(self, targetname, bugzilla_email):
        person = People.by_username(turbogears.identity.current.user_name)
        target = People.by_username(targetname)

        if not can_edit_user(person, target):
            turbogears.flash(_("You do not have permission to edit '%s'") % target.username)
            turbogears.redirect('/bugzilla')
            return dict()

        new_configs = {'bugzilla_email': bugzilla_email}
        cur_configs = Configs.query.filter_by(person_id=target.id, application='bugzilla').all()

        if bugzilla_email == None:
          session.delete(cur_configs[0])
          turbogears.flash(_("Bugzilla specific email removed!  This means your bugzilla email must be set to: %s" % target.email))
          turbogears.redirect('/bugzilla/')
        for config in cur_configs:
            for new_config in new_configs.keys():
                if config.attribute == new_config:
                    config.value = new_configs[new_config]
                    del(new_configs[new_config])
        for config in new_configs:
            c = Configs(application='bugzilla', attribute=config, value=new_configs[config])
            target.configs.append(c)

        turbogears.flash(_("Changes saved.  Please allow up to 1 hour for changes to be realized."))
        turbogears.redirect('/bugzilla/')
        return dict()