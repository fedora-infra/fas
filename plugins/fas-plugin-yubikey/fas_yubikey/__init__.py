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

admin_group = config.get('admingroup', 'accounts')
system_group = config.get('systemgroup', 'fas-system')
thirdparty_group = config.get('thirdpartygroup', 'thirdparty')

class YubikeySave(validators.Schema):
    targetname = KnownUser
    yubikey_enabled = validators.OneOf(['0', '1'], not_empty=True)
    yubikey_prefix = validators.String(min=12, max=12, not_empty=True)

def get_configs(configs_list):
    configs = {}
    for config in configs_list:
        configs[config.attribute] = config.value
    if 'enabled' not in configs:
        configs['enabled'] = '0'
    if 'prefix' not in configs:
        configs['prefix'] = 'Not Defined'
    return configs

class AuthException(BaseException): pass

def otp_verify(uid, otp):
    import sys, os, re
    import urllib2
    client_id='2431'

    target = People.by_id(uid)
    configs = get_configs(Configs.query.filter_by(person_id=target.id, application='yubikey').all())

    if not otp.startswith(configs['prefix']):
      raise AuthException('Unauthorized/Invalid OTP')


    server_prefix = 'http://api.yubico.com/wsapi/verify?id='
    auth_regex = re.compile('^status=(?P<rc>\w{2})')

    server_url = server_prefix + client_id + "&otp=" + otp

    fh = urllib2.urlopen(server_url)

    for line in fh:
      match = auth_regex.search(line.strip('\n'))
      if match:
        if match.group('rc') == 'OK':
          return
        else:
          raise AuthException(line.split('=')[1])
        break

    turbogears.redirect('/yubikey/')
    return dict()


class YubikeyPlugin(controllers.Controller):
    capabilities = ['yubikey_plugin']

    def __init__(self):
        '''Create Yubikey Controller.'''
        self.path = ''

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas_yubikey.templates.index")
    def index(self):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if turbogears.identity.current.user_name == username:
            personal = True
        else:
            personal = False
        # TODO: We can do this without a db lookup by using something like
        # if groupname in identity.groups: pass
        # We may want to do that in is_admin() though. -Toshio
        user = People.by_username(turbogears.identity.current.user_name)
        if is_admin(user):
            admin = True
        else:
            admin = False
        if turbogears.identity.current.user_name == username:
            personal = True
        else:
            personal = False

        configs = get_configs(Configs.query.filter_by(person_id=person.id, application='yubikey').all())
        return dict(admin=admin, person=person, personal=personal, configs=configs)

    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)


    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas_yubikey.templates.edit")
    def edit(self, targetname=None):
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        target = People.by_username(targetname)
        admin = is_admin(person)
        configs = get_configs(Configs.query.filter_by(person_id=target.id, application='yubikey').all())
        return dict(admin=admin, person=person, configs=configs,target=target)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=YubikeySave())
    @error_handler(error)
    @expose(template='fas_yubikey.templates.edit')
    def save(self, targetname, yubikey_enabled, yubikey_prefix):
        person = People.by_username(turbogears.identity.current.user_name)
        target = People.by_username(targetname)
        if not can_edit_user(person, target):
            turbogears.flash(_("You do not have permission to edit '%s'") % target.username)
            turbogears.redirect('/yubikey')
            return dict()

        new_configs = {'enabled': yubikey_enabled, 'prefix': yubikey_prefix}
        cur_configs = Configs.query.filter_by(person_id=target.id, application='yubikey').all()

        for config in cur_configs:
            for new_config in new_configs.keys():
                if config.attribute == new_config:
                    config.value = new_configs[new_config]
                    del(new_configs[new_config])
        for config in new_configs:
            c = Configs(application='yubikey', attribute=config, value=new_configs[config])
            target.configs.append(c)

        turbogears.flash(_("Changes saved.  Please allow up to 1 hour for changes to be realized."))
        turbogears.redirect('/yubikey/')
        return dict()

    @error_handler(error)
    @expose(format="json", allow_json=True)
    def self_test(self, uid, otp):
        try:
          otp_verify(uid, otp)
          turbogears.flash(_("Yubikey auth success."))
        except AuthException, error:
          turbogears.flash(_("Yubikey auth Failed: %s." % error))

        turbogears.redirect('/yubikey/')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(format="json", allow_json=True)
    def dump(self):
        person = People.by_username(identity.current.user_name)
        if identity.in_group(admin_group) or \
            identity.in_group(system_group):
            yubikey_attrs = {}
            for attr in Configs.query.filter_by(application='yubikey').all():
                if attr.person_id not in yubikey_attrs:
                    yubikey_attrs[attr.person_id] = {}
                yubikey_attrs[attr.person_id][attr.attribute] = attr.value
            return dict(yubikey_attrs=yubikey_attrs)
        return dict()
    
    @expose(template="fas.templates.help")
    def help(self, id='none'):
        help = { 'none' :               [_('Error'), _('<p>We could not find that help item</p>')],
            'yubikey_prefix':        [_('Yubikey Prefix'), _('<p>The first 12 characters of a yubikey ID</p>')],
            'yubikey_enabled':        [_('Yubikey Enabled'), _('<p>When enabled, yubikey authentication will be available to you when using our services.</p>')],
            'yubikey_test':        [_('Yubikey Test'), _('<p>Test your yubikey against FAS server.</p>')]
            }

        try:
            helpItem = help[id]
        except KeyError:
            return dict(title=_('Error'), helpItem=[_('Error'), _('<p>We could not find that help item</p>')])
        return dict(help=helpItem)

    
    @classmethod
    def initPlugin(cls, controller):
        cls.log = logging.getLogger('plugin.yubikey')
        cls.log.info('Yubikey plugin initializing')
        try:
            path, self = controller.requestpath(cls, '/yubikey')
            cls.log.info('Yubikey plugin hooked')
            self.path = path
            if self.sidebarentries not in sidebar.entryfuncs:
                sidebar.entryfuncs.append(self.sidebarentries)
        except (plugin.BadPathException,
            plugin.PathUnavailableException), e:
            cls.log.info('Yubikey plugin hook failure: %s' % e)

    def delPlugin(self, controller):
        self.log.info('Yubikey plugin shutting down')
        if self.sidebarentries in sidebar.entryfuncs:
            sidebar.entryfuncs.remove(self.sidebarentries)

    def sidebarentries(self):
        return [('Yubikey', self.path)]
