# -*- coding: utf-8 -*-
import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import metadata, mapper, get_engine, session
from sqlalchemy import Table, Column, Integer, String, MetaData, Boolean, create_engine
from sqlalchemy.exc import IntegrityError

import cherrypy
import turbomail

from genshi.template.plugin import TextTemplateEnginePlugin

import fas.sidebar as sidebar
import logging
import fas.plugin as plugin

from fas.model import People, PeopleTable, PersonRolesTable, GroupsTable, Configs
from fas.model import Log

from fas.auth import *
from fas.user import KnownUser
from fas.util import available_languages

from random import choice
import time, string

import fancyflash as ff
## Set the default timeout for message box display
ff.set_default_flash_timeout(5)
## Let FancyFlashWidget be included on every page
ff.register_flash_widget()

ykksm_db_uri = config.get('ykksm_db')
ykval_db_uri = config.get('ykval_db')

ykksm_metadata = MetaData(ykksm_db_uri)
ykval_metadata = MetaData(ykval_db_uri)

ykksm_table = Table('yubikeys', ykksm_metadata,
                Column('serialnr', Integer, primary_key=True),
                Column('publicname', String, nullable=False),
                Column('created', String, nullable=False),
                Column('internalname', String, nullable=False),
                Column('aeskey', String, nullable=False),
                Column('lockcode', String, nullable=False),
                Column('creator', String, nullable=False),
                Column('active', Boolean, default=True),
                Column('hardware', Boolean, default=True) )

ykval_table = Table('yubikeys', ykval_metadata,
                Column('active', Boolean, default=True),
                Column('created', Integer, nullable=False),
                Column('modified', Integer, nullable=False),
                Column('yk_publicname', String, primary_key=True),
                Column('yk_counter', Integer, nullable=False),
                Column('yk_use', Integer, nullable=False),
                Column('yk_low', Integer, nullable=False),
                Column('yk_high', Integer, nullable=False),
                Column('nonce', String, default=''),
                Column('notes', String, default='') )


class Ykksm(object):
    def __init__(self, serialnr, publicname, created, internalname, aeskey, lockcode, creator, active=True, hardware=True):
        self.serialnr = serialnr
        self.publicname = publicname
        self.created = created
        self.internalname = internalname
        self.aeskey = aeskey
        self.lockcode = lockcode
        self.creator = creator
        self.active = active
        self.hardware = hardware

class Ykval(object):
    def __init__(self, active, created, modified, yk_publicname, yk_counter, yk_use, yk_low, yk_high, nonce, notes):
        self.active = active
        self.created = created
        self.modified = modified
        self.yk_publicname = yk_publicname
        self.yk_counter = yk_counter
        self.yk_use = yk_use
        self.yk_low = yk_low
        self.yk_high = yk_high
        self.nonce = nonce
        self.notes = notes

mapper(Ykksm, ykksm_table)
mapper(Ykval, ykval_table)

import subprocess

admin_group = config.get('admingroup', 'accounts')
system_group = config.get('systemgroup', 'fas-system')
thirdparty_group = config.get('thirdpartygroup', 'thirdparty')
client_id = '1'

class YubikeySave(validators.Schema):
    targetname = KnownUser
    yubikey_enabled = validators.OneOf(['0', '1'], not_empty=True)
    yubikey_prefix = validators.String(min=12, max=12, not_empty=False)

def get_configs(configs_list):
    configs = {}
    for config in configs_list:
        configs[config.attribute] = config.value
    if 'enabled' not in configs:
        configs['enabled'] = '0'
    if 'prefix' not in configs:
        configs['prefix'] = _('Not Defined')
    return configs

class AuthException(Exception): pass

def otp_verify(uid, otp):
    import sys, os, re
    import urllib2

    target = People.by_id(uid)
    configs = get_configs(Configs.query.filter_by(person_id=target.id, application='yubikey').all())

    if not otp.startswith(configs['prefix']):
      raise AuthException('Unauthorized/Invalid OTP')


    server_prefix = 'http://localhost/yk-val/verify?id='
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

def hex2modhex (string):
    ''' Convert a hex string to a modified hex string '''
    replacement = { '0': 'c',
                    '1': 'b',
                    '2': 'd',
                    '3': 'e',
                    '4': 'f',
                    '5': 'g',
                    '6': 'h',
                    '7': 'i',
                    '8': 'j',
                    '9': 'k',
                    'a': 'l',
                    'b': 'n',
                    'c': 'r',
                    'd': 't',
                    'e': 'u',
                    'f': 'v' }
    new_string = ''
    for letter in string:
        new_string = new_string + replacement[letter]
    return new_string

def gethexrand(length):
    return ''.join([choice('0123456789abcdef') for i in range(length)]).lower()



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

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template='json')
    def genkey(self):
        
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        created = time.strftime("%Y-%m-%dT%H:%M:%S")
        hexctr = "%012x" % person.id
        publicname = hex2modhex(hexctr)
        internalname = gethexrand(12)
        aeskey = gethexrand(32)
        lockcode = gethexrand(12)

        try:
            new_ykksm = Ykksm(serialnr=person.id, publicname=publicname, created=created, internalname=internalname, aeskey=aeskey, lockcode=lockcode, creator=username)
            session.add(new_ykksm)
            session.flush() 
        except IntegrityError:
            session.rollback()
            old_ykksm = session.query(Ykksm).filter_by(serialnr=person.id).all()[0]
            session.delete(old_ykksm)
            new_ykksm = Ykksm(serialnr=person.id, publicname=publicname, created=created, internalname=internalname, aeskey=aeskey, lockcode=lockcode, creator=username)
            old_ykksm = new_ykksm
            session.flush()
        try:
            old_ykval = session.query(Ykval).filter_by(yk_publicname=publicname).all()[0]
            session.delete(old_ykval)
            session.flush()
        except IndexError:
            # No old record?  Maybe they never used their key
            pass
            
        string = "%s %s %s" % (publicname, internalname, aeskey)
        return dict(key=string)

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
            ff.error(_("You do not have permission to edit '%s'") % target.username)
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
        mail_subject=_('Fedora Yubikey changed for %s' % target)
        mail_text=_('''
You have changed your Yubikey on your Fedora account %s. If you did not make
this change, please contact admin@fedoraproject.org''' % target)
        email='%s@fedoraproject.org' % target
        send_mail(email, mail_subject, mail_text)
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
          ff.error(_("Yubikey auth Failed: %s." % error))

        turbogears.redirect('/yubikey/')
        return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @expose(format="text", allow_json=True)
    def dump(self):
        dump_list = []
        person = People.by_username(identity.current.user_name)
        if identity.in_group(admin_group) or \
            identity.in_group(system_group):
            yubikey_attrs = {}
            for attr in Configs.query.filter_by(application='yubikey').all():
                if attr.person_id not in yubikey_attrs:
                    yubikey_attrs[attr.person_id] = {}
                yubikey_attrs[attr.person_id][attr.attribute] = attr.value
            for user_id in yubikey_attrs:
                if yubikey_attrs[user_id]['enabled'] == u'1':
                    dump_list.append('%s:%s' % (People.by_id(user_id).username, yubikey_attrs[user_id]['prefix']))
            return '\n'.join(dump_list)
        return '# Sorry, must be in an admin group to get these'
    
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
        return [(_('Yubikey'), self.path)]

def send_mail(to_addr, subject, text, from_addr=None):
    if from_addr is None:
        from_addr = config.get('accounts_email')
    message = turbomail.Message(from_addr, to_addr, subject)
    message.plain = text
    turbomail.enqueue(message)

