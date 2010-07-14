# -*- coding: utf-8 -*-
import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import cherrypy

from genshi.template.plugin import TextTemplateEnginePlugin

import re

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

class ValidAsteriskPass(validators.FancyValidator):
    pass_regex = re.compile(r'^\d+$')

    messages = {'invalid_pass': _('The password must be numeric and be at least 6 digits long.') }

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if not self.username_regex.match(value):
            raise validators.Invalid(self.message('invalid_pass', state,
                username=value), value, state)

class AsteriskSave(validators.Schema):
    targetname = KnownUser
    asterisk_enabled = validators.OneOf(['0', '1'], not_empty=True)
    asterisk_pass = validators.All(
        ValidAsteriskPass,
        validators.String(min=6, not_empty=True),
    )

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
        if not cla_done(person):
            turbogears.flash(_('You must sign the CLA to have access to this service.'))
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
        if not cla_done(target):
            turbogears.flash(_('You must sign the CLA to have access to this service.'))
            turbogears.redirect('/user/view/%s' % target.username)
            return dict()
        admin = is_admin(person)
        configs = get_configs(Configs.query.filter_by(person_id=target.id, application='asterisk').all())
        return dict(admin=admin, person=person, configs=configs,target=target)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=AsteriskSave())
    @error_handler(error)
    @expose(template='fas_asterisk.templates.edit')
    def save(self, targetname, asterisk_enabled, asterisk_pass):
        person = People.by_username(turbogears.identity.current.user_name)
        target = People.by_username(targetname)
        if not cla_done(target):
            turbogears.flash(_('You must sign the CLA to have access to this service.'))
            turbogears.redirect('/user/view/%s' % target.username)
            return dict()
        
        if not can_edit_user(person, target):
            turbogears.flash(_("You do not have permission to edit '%s'") % target.username)
            turbogears.redirect('/asterisk')
            return dict()

        new_configs = {'enabled': asterisk_enabled, 'pass': asterisk_pass}
        cur_configs = Configs.query.filter_by(person_id=target.id, application='asterisk').all()

        for config in cur_configs:
            for new_config in new_configs.keys():
                if config.attribute == new_config:
                    config.value = new_configs[new_config]
                    del(new_configs[new_config])
        for config in new_configs:
            c = Configs(application='asterisk', attribute=config, value=new_configs[config])
            target.configs.append(c)

        turbogears.flash(_("Changes saved.  Please allow up to 1 hour for changes to be realized."))
        turbogears.redirect('/asterisk/')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(format="json", allow_json=True)
    def dump(self):
        person = People.by_username(identity.current.user_name)
        if identity.in_group(admin_group) or \
            identity.in_group(system_group):
            asterisk_attrs = {}
            for attr in Configs.query.filter_by(application='asterisk').all():
                if attr.person_id not in asterisk_attrs:
                    asterisk_attrs[attr.person_id] = {}
                asterisk_attrs[attr.person_id][attr.attribute] = attr.value
            return dict(asterisk_attrs=asterisk_attrs)
        return dict()
    
    @expose(template="fas.templates.help")
    def help(self, id='none'):
        help = { 'none' :               [_('Error'), _('<p>We could not find that help item</p>')],
            'asterisk_pass':        [_('Asterisk Password'), _('<p>Your Asterisk password needs to be numeric only and should not match your Fedora Password.  <b> You will use this password to log in to asterisk <u>not</u> your normal user account password.</b></p>')],
            'asterisk_enabled':     [_('Asterisk Active?'), _('<p>If set to false, your asterisk extension will not exist and you will not get calls nor be able to log in.  If set to enabled you will be able to receive calls and log in</p>')],
            'asterisk_voicemail':   [_('Asterisk Voicemail'), _('<p>Would you like to receive voice mail when people call and you are not around?  It will come to you via email and an attachment</p>')],
            'asterisk_sms':         [_('Asterisk SMS Notification'), _('<p>When someone leaves you an email, a notification will get sent to this address.  It will not contain the actual message, just a notification that a message is waiting.</p>')],
            'asterisk_extension':   [_('Asterisk Extension'), _('<p>This is your extension number.  Others can reach you via this number or via your sip address.</p>')],
            'asterisk_sip_address': [_('Asterisk SIP Address'), _('<p>This is your SIP address.  When using phones that support it (or Ekiga or Twinkle for example) people can contact you by typing this address.</p>')],
            }

        try:
            helpItem = help[id]
        except KeyError:
            return dict(title=_('Error'), helpItem=[_('Error'), _('<p>We could not find that help item</p>')])
        return dict(help=helpItem)

    
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
