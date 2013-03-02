# -*- coding: utf-8 -*-
''' Provides user IO to FAS '''
#
# Copyright © 2008  Ricky Zhou
# Copyright © 2008-2011 Red Hat, Inc.
# Copyright © 2012  Patrick Uiterwijk
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
#            Toshio Kuratomi <toshio@redhat.com>
#            Patrick Uiterwijk <puiterwijk@fedoraproject.org>

# @error_handler() takes a reference to the error() method defined in the
# class (E0602)

try:
    from bunch import Bunch
except ImportError:
    from fedora.client import DictContainer as Bunch

import turbogears
from turbogears import controllers, expose, identity, \
        validate, validators, error_handler, config, redirect
from turbogears.database import session
import cherrypy
from tgcaptcha2 import CaptchaField
from tgcaptcha2.validator import CaptchaFieldValidator

from fas.util import send_mail
from fas.lib.gpg import encrypt_text

import os
import re
import gpgme
import StringIO
import crypt
import string
import subprocess
from OpenSSL import crypto

if config.get('use_openssl_rand_bytes', False):
    from OpenSSL.rand import bytes as rand_bytes
else:
    from os import urandom as rand_bytes

import pytz
from datetime import datetime
import time

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.sql import select

from fedora.tg.utils import request_format

import fas.fedmsgshim

import fas
from fas.model import PeopleTable, PersonRolesTable, GroupsTable
from fas.model import People, PersonRoles, Groups, Log
from fas import openssl_fas
from fas.auth import is_admin, cla_done, undeprecated_cla_done, can_edit_user
from fas.util import available_languages
from fas.validators import KnownUser, PasswordStrength, ValidSSHKey, \
        NonFedoraEmail, ValidLanguage, UnknownUser, ValidUsername, \
        ValidHumanWithOverride
from fas import _

#ADMIN_GROUP = config.get('admingroup', 'accounts')
#system_group = config.get('systemgroup', 'fas-system')
#thirdparty_group = config.get('thirdpartygroup', 'thirdparty')

CAPTCHA = CaptchaField(name='captcha', label=_('Solve the math problem'))

class UserCreate(validators.Schema):
    ''' Validate information for a new user '''
    username = validators.All(
        UnknownUser,
        ValidUsername(not_empty=True),
        validators.UnicodeString(max=32, min=3),
    )
    human_name = validators.All(
        validators.UnicodeString(not_empty=True),
        )
    human_name_override = validators.All(
        )
    email = validators.All(
        validators.Email(not_empty=True, strip=True),
        NonFedoraEmail(not_empty=True, strip=True),
    )
    verify_email = validators.All(
        validators.Email(not_empty=True, strip=True),
        NonFedoraEmail(not_empty=True, strip=True),
    )
    security_question = validators.UnicodeString(not_empty=True)
    security_answer = validators.UnicodeString(not_empty=True)
    #fedoraPersonBugzillaMail = validators.Email(strip=True)
    postal_address = validators.UnicodeString(max=512)
    captcha = CaptchaFieldValidator()
    chained_validators = [ validators.FieldsMatch('email', 'verify_email'),
                           ValidHumanWithOverride('human_name', 'human_name_override') ]

class UserSetSecurityQuestion(validators.Schema):
    ''' Validate new security question and answer '''
    currentpassword = validators.UnicodeString(not_empty=True)
    newquestion = validators.UnicodeString(not_empty=True)
    newanswer = validators.UnicodeString(not_empty=True)

class UserSetPassword(validators.Schema):
    ''' Validate new and old passwords '''
    currentpassword = validators.UnicodeString(not_empty=True)
    password = PasswordStrength(not_empty=True)
    passwordcheck = validators.UnicodeString(not_empty=True)
    chained_validators = [validators.FieldsMatch('password', 'passwordcheck')]

class UserResetPassword(validators.Schema):
    password = PasswordStrength(not_empty=True)
    passwordcheck = validators.UnicodeString(not_empty=True)
    chained_validators = [validators.FieldsMatch('password', 'passwordcheck')]

class UserSave(validators.Schema):
    targetname = KnownUser
    human_name = validators.All(
       validators.UnicodeString(not_empty=True, max=42),
       validators.Regex(regex='^[^\n:<>]+$'),
    )
    ircnick = validators.UnicodeString(max=42)
    status = validators.OneOf([
        'active', 'inactive', 'expired', 'admin_disabled'])
    ssh_key = ValidSSHKey(max=5000)
    gpg_keyid = validators.UnicodeString  # TODO - could use better validation
    telephone = validators.UnicodeString  # TODO - could use better validation
    email = validators.All(
       validators.Email(not_empty=True, strip=True, max=128),
       NonFedoraEmail(not_empty=True, strip=True, max=128),
    )
    locale = ValidLanguage(not_empty=True, strip=True)
    #fedoraPersonBugzillaMail = validators.Email(strip=True, max=128)
    #fedoraPersonKeyId- Save this one for later :)
    postal_address = validators.UnicodeString(max=512)
    timezone = validators.UnicodeString   # TODO - could use better validation
    country_code = validators.UnicodeString(max=2, strip=True)
    privacy = validators.Bool
    latitude = validators.Number
    longitude = validators.Number
    comments = validators.UnicodeString   # TODO - could use better validation

def generate_password(password=None, length=16):
    ''' Generate Password

    :arg password: Plain text password to be crypted.  Random one generated
                    if None.
    :arg length: Length of password to generate.
    returns: crypt.crypt utf-8 password
    '''
    secret = {} # contains both hash and password

    # From crypt(3) manpage.
    salt_charset = string.ascii_letters + string.digits + './'
    salt = random_string(salt_charset, 16)
    hash_id = '6' # SHA-512
    salt_str = '$' + hash_id + '$' + salt

    if password is None:
        password_charset = string.ascii_letters + string.digits
        password = random_string(password_charset, length)

    secret['hash'] = crypt.crypt(password.encode('utf-8'), salt_str)
    secret['pass'] = password

    return secret

def random_string(charset, length):
    '''Generates a random string for password and salts.

    This use a pseudo-random number generator suitable for cryptographic
    use, such as /dev/urandom or (better) OpenSSL's RAND_bytes.

    :arg length: Length of salt to be generated
    :returns: String of salt
    '''
    s = ''

    while length > 0:
        r = rand_bytes(length)
        for c in r:
            # Discard all bytes that aren't in the charset.  This is the
            # simplest way to ensure that the function is not biased.
            if c in charset:
                s += c
                length -= 1

    return s

class User(controllers.Controller):
    ''' Our base User controller for user based operations '''
    # Regex to tell if something looks like a crypted password
    crypted_password_re = re.compile('^\$[0-9]\$.*\$.*')

    def __init__(self):
        '''Create a User Controller.
        '''

    @identity.require(identity.not_anonymous())
    def index(self):
        '''Redirect to view
        '''
        redirect('/user/view/%s' % identity.current.user_name)

    def json_request(self):
        ''' Determines if the request is for json or not_

        :returns: true if the request is json, else false
        '''
        return 'tg_format' in cherrypy.request.params and \
                cherrypy.request.params['tg_format'] == 'json'


    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(identity.not_anonymous())
    @validate(validators= {'username': KnownUser })
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.view", allow_json=True)
    def view(self, username=None):
        '''View a User.
        '''
        show = {}
        show['show_postal_address'] = config.get('show_postal_address')
        if not username:
            username = identity.current.user_name
        person = People.by_username(username)
        if identity.current.user_name == username:
            personal = True
        else:
            personal = False
        admin = is_admin(identity.current)
        (cla, undeprecated_cla) = undeprecated_cla_done(person)
        person_data = person.filter_private()
        person_data['approved_memberships'] = list(person.approved_memberships)
        person_data['unapproved_memberships'] = list(person.unapproved_memberships)
        person_data['roles'] = person.roles

        roles = person.roles
        roles.json_props = {
                'PersonRole': ('group',),
                'Groups': ('unapproved_roles',),
                }
        return dict(person=person_data, cla=cla, undeprecated=undeprecated_cla, personal=personal,
                admin=admin, show=show)

    @identity.require(identity.not_anonymous())
    @validate(validators={ 'targetname' : KnownUser })
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.edit")
    def edit(self, targetname=None):
        '''Edit a user
        '''
        show = {}
        show['show_postal_address'] = config.get('show_postal_address')
        languages = available_languages()

        username = identity.current.user_name
        person = People.by_username(username)

        admin = is_admin(identity.current)

        if targetname:
            target = People.by_username(targetname)
        else:
            target = People.by_username(identity.current.user_name)

        if not can_edit_user(person, target):
            turbogears.flash(_('You cannot edit %s') % target.username)
            turbogears.redirect('/user/view/%s' % target.username)
            return dict()

        target = target.filter_private()
        return dict(target=target, languages=languages, admin=admin, show=show)

    # A float(n) function, that can safely be called with a None-argument
    def _safe_float(self, f):
        if f:
            return float(f)
        else:
            return None

    @identity.require(identity.not_anonymous())
    @validate(validators=UserSave())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.user.edit')
    def save(self, targetname, human_name, telephone, email, status,
            postal_address=None, ssh_key=None, ircnick=None, gpg_keyid=None,
             comments='', locale='en', timezone='UTC', country_code='',
             latitude=None, longitude=None, privacy=False):
        ''' Saves user information to database

        :arg targetname: Target user to alter
        :arg human_name: Human name of target user
        :arg telephone: Telephone number of target user
        :arg email: Email address of target user
        :arg status: Status of target user
        :arg postal_address: Mailing address of target user
        :arg ssh_key: ssh key of target user
        :arg ircnick: IRC nick of the target user
        :arg gpg_keyid: gpg key id of target user
        :arg comments: Misc comments about target user
        :arg locale: Locale of the target user for language purposes
        :arg timezone: Timezone of target user
        :arg country_code: Country Code of target user
        :arg latitude: Latitude of target user
        :arg privacy: Determine if the user info should be private for user

        :returns: empty dict
        '''

        # person making changes
        username = identity.current.user_name
        person = People.by_username(username)

        # Account being changed
        target = People.by_username(targetname)

        emailflash = ''
        changed = [] # record field names that changed for fedmsg

        if not can_edit_user(person, target):
            turbogears.flash(_("You do not have permission to edit '%s'") % \
                target.username)
            turbogears.redirect('/user/view/%s', target.username)
            return dict()

        try:
            if target.status != status:
                if (status in ('expired', 'admin_disabled') or target.status \
                    in ('expired', 'admin_disabled')) and \
                    not is_admin(person):
                    turbogears.flash(_(
                        'Only admin can enable or disable an account.'))
                    return dict()
                else:
                    # TODO: revoke cert
                    target.old_password = target.password
                    target.password = '*'
                    for group in target.unapproved_memberships:
                        try:
                            target.remove(group, person)
                        except fas.RemoveError:
                            pass
                Log(author_id=person.id, description=
                    '%(person)s\'s status changed from %(old)s to %(new)s' % \
                    {'person': target.username,
                     'old': target.status,
                     'new': status})
                target.status = status
                target.status_change = datetime.now(pytz.utc)
                changed.append('status')

            if target.email != email:
                test = select([PeopleTable.c.username],
                        func.lower(PeopleTable.c.email) \
                        == email.lower()).execute().fetchall()
                if test:
                    turbogears.flash(_(
                        'Somebody is already using that email address.'
                    ))
                    turbogears.redirect("/user/edit/%s" % target.username)
                    return dict()

                emailflash = _('Before your new email takes effect, you ' + \
                    'must confirm it.  You should receive an email with ' + \
                    'instructions shortly.')
                token_charset = string.ascii_letters + string.digits
                token = random_string(token_charset, 32)
                target.unverified_email = email
                target.emailtoken = token
                change_subject = _('Email Change Requested for %s') % \
                    person.username
                change_text = _('''
You have recently requested to change your Fedora Account System email
to this address.  To complete the email change, you must confirm your
ownership of this email by visiting the following URL (you will need to
login with your Fedora account first):

%(verifyurl)s/accounts/user/verifyemail/%(token)s
''') % { 'verifyurl' : config.get('base_url_filter.base_url').rstrip('/'), 'token' : token}
                send_mail(email, change_subject, change_text)
                # Note: email is purposefully not added to the changed[] list
                # here because we don't change it until the new email is
                # verified (in a separate method)

            # note, ssh_key is often None or empty string at this point
            # (file upload).  Testing ssh_key first prevents removing the
            # ssh_key in this case.  The clearkey() method is used for removing
            # an ssh_key.
            if ssh_key and target.ssh_key != ssh_key:
                target.ssh_key = ssh_key
                changed.append('ssh_key')

            # latitude and longitude are tricky.  They may be floats or ints
            # coming from the web app.  They're floats coming from the db
            if target.latitude != self._safe_float(latitude):
                target.latitude = self._safe_float(latitude)
                changed.append('latitude')
            
            if target.longitude != self._safe_float(longitude):
                target.longitude = self._safe_float(longitude)
                changed.append('longitude')

            # Other fields don't need any special handling
            fields = ('human_name', 'telephone', 'postal_address', 'ircnick',
                      'gpg_keyid', 'comments', 'locale', 'timezone',
                      'country_code', 'privacy')
            for field in fields:
                if getattr(target, field) != locals()[field]:
                    setattr(target, field, locals()[field])
                    changed.append(field)

        except TypeError, error:
            turbogears.flash(_('Your account details could not be saved: %s')
                % error)
            turbogears.redirect("/user/edit/%s" % target.username)
            return dict()
        else:
            change_subject = _('Fedora Account Data Update %s') % \
                target.username
            change_text = _('''
You have just updated information about your account.  If you did not request
these changes please contact admin@fedoraproject.org and let them know.  Your
updated information is:

  username:       %(username)s
  full name:      %(fullname)s
  ircnick:        %(ircnick)s
  telephone:      %(telephone)s
  locale:         %(locale)s
  timezone:       %(timezone)s
  country code:   %(country_code)s
  latitude:       %(latitude)s
  longitude:      %(longitude)s
  privacy flag:   %(privacy)s
  ssh_key:        %(ssh_key)s
  gpg_keyid:      %(gpg_keyid)s

If the above information is incorrect, please log in and fix it:

   %(editurl)s/accounts/user/edit/%(username)s
''') % { 'username'       : target.username,
         'fullname'       : target.human_name,
         'ircnick'        : target.ircnick,
         'telephone'      : target.telephone,
         'locale'         : target.locale,
         'timezone'       : target.timezone,
         'country_code'   : target.country_code,
         'latitude'       : target.latitude,
         'longitude'      : target.longitude,
         'privacy'        : target.privacy,
         'ssh_key'        : target.ssh_key,
         'gpg_keyid'      : target.gpg_keyid,
         'editurl'        : config.get('base_url_filter.base_url').rstrip('/')}
            send_mail(target.email, change_subject, change_text)
            turbogears.flash(_('Your account details have been saved.') + \
                '  ' + emailflash)

            fas.fedmsgshim.send_message(topic="user.update", msg={
                'agent': person.username,
                'user': target.username,
                'fields': changed,
            })
            turbogears.redirect("/user/view/%s" % target.username)
            return dict()

    @identity.require(identity.not_anonymous())
    @expose(template="fas.templates.user.list", allow_json=True)
    def dump(self, search=u'a*', groups=''):
        ''' Return a list of users sorted by search

        :arg search: Search wildcard (a* or *blah*) to filter by usernames
        :arg groups: Filter by specific groups

        :returns: dict of people, unapproved_paople and search string
        '''
        groups_to_return_list = groups.split(',')
        groups_to_return = []
        # Special Logic, find out all the people who are in more then one group
        if '@all' in groups_to_return_list:
            groups_results = Groups.query().filter(Groups.group_type!='cla')
            for group in groups_results:
                groups_to_return.append(group.name)

        for group_type in groups_to_return_list:
            if group_type.startswith('@'):
                group_list = Groups.query.filter(Groups.group_type.in_(
                    [group_type.strip('@')]))
                for group in group_list:
                    groups_to_return.append(group.name)
            else:
                groups_to_return.append(group_type)
        people = People.query.join('roles').filter(
            PersonRoles.role_status=='approved').join(
            PersonRoles.group).filter(Groups.name.in_( groups_to_return ))

        # p becomes what we send back via json
        people_dict = []
        for strip_p in people:
            strip_p = strip_p.filter_private()
            if strip_p.status == 'active':
                people_dict.append({
                    'username'  : strip_p.username,
                    'id'        : strip_p.id,
                    'ssh_key'   : strip_p.ssh_key,
                    'human_name': strip_p.human_name,
                    'password'  : strip_p.password
                    })

        return dict(people=people_dict, unapproved_people=[], search=search)

    #class UserList(validators.Schema):
    #   search = validators.UnicodeString()
    #   fields = validators.Set()
    #   limit = validators.Int()
    #@validate(validators=UserList())
    @identity.require(identity.not_anonymous())
    @expose(template="fas.templates.user.list", allow_json=True)
    def list(self, search=u'a*', fields=None, limit=None):
        '''List users

        :kwarg search: Limit the users returned by the search string.  * is a
            wildcard character.
        :kwarg fields: Fields to return in the json request.  Default is
            to return everything.

        This should be fixed up at some point.  Json data needs at least the
        following for fasClient to work::

          list of users with these attributes:
            username
            id
            ssh_key
            human_name
            password

        The template, on the other hand, needs to know about::

          list of usernames with information about whether the user is
          approved in cla_done

        supybot-fedora uses the email attribute

        The json information is useful so we probably want to create a new
        method for it at some point.  One which returns the list of users with
        more complete information about themselves.  Then this method can
        change to only returning username and cla status.
        '''
        ### FIXME: Should port this to a validator
        # Work around a bug in TG (1.0.4.3-2)
        # When called as /user/list/*  search is a str type.
        # When called as /user/list/?search=* search is a unicode type.
        if not search:
            search = u'*'
        if not isinstance(search, unicode) and isinstance(search, basestring):
            search = unicode(search, 'utf-8', 'replace')

        re_search = search.translate({ord(u'*'): ur'%'}).lower()

        if isinstance(fields, basestring):
            # If a string, then make a list
            fields = [fields]
        elif fields:
            # This makes sure the field is a list
            fields = list(fields)
        else:
            fields = []

        # Ensure limit is a valid number
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None

        # Set a reasonable default limit for web interface results
        if not limit and request_format() != 'json':
            limit = 100

        joined_roles = PeopleTable.outerjoin(PersonRolesTable,
                onclause=PersonRolesTable.c.person_id==PeopleTable.c.id)\
                    .outerjoin(GroupsTable,
                    onclause=PersonRolesTable.c.group_id==GroupsTable.c.id)
        stmt = select([joined_roles]).where(People.username.ilike(re_search))\
                .order_by(People.username).limit(limit)
        stmt.use_labels = True
        people = stmt.execute()

        people_map = dict()
        group_map = dict()

        # This replicates what filter_private does.  At some point we might
        # want to figure out a way to pull this into a function
        if identity.in_any_group(config.get('admingroup', 'accounts'),
            config.get('systemgroup', 'fas-system')):
            # Admin and system are the same for now
            user = 'admin'
        elif identity.current.anonymous:
            user = 'anonymous'
        else:
            user = 'public'
        # user_perms is a synonym for user with one difference
        # If user is public then we end up changing user_perms
        # depending on whether the record is for the user themselves and if
        # the record has privacy set
        user_perms = user

        for record in people:
            if record.people_username not in people_map:
                # Create a new person
                person = Bunch()
                if user == 'public':
                    # The general public gets different fields depending on
                    # the record being accessed
                    if identity.current.user_name == record.people_username:
                        user_perms = 'self'
                    elif record.people_privacy:
                        user_perms = 'privacy'
                    else:
                        user_perms = 'public'

                # Clear all the fields so the client side doesn't get KeyError
                for field in People.allow_fields['complete']:
                    person[field] = None

                # Fill in the people record
                for field in People.allow_fields[user_perms]:
                    person[field] = record['people_%s' % field]
                if identity.in_group(config.get('thirdpartygroup',
                    'thirdparty')):
                    # Thirdparty is a little strange as it has to obey the
                    # privacy flag just like a normal user but we allow a few
                    # fields to be sent on in addition (ssh_key for now)
                    for field in People.allow_fields['thirdparty']:
                        person[field] = record['people_%s' % field]
                # Make sure the password field is a default value that won't
                # cause issue for scripts
                if 'password' not in People.allow_fields[user_perms]:
                    person.password = '*'

                person.group_roles = {}
                person.memberships = []
                person.roles = []
                people_map[record.people_username] = person
            else:
                # We need to have a reference to the person since we're
                # going to add a group to it
                person = people_map[record.people_username]

            if record.groups_name not in group_map:
                # Create the group
                group = Bunch()
                group.id = record.groups_id
                group.display_name = record.groups_display_name
                group.name = record.groups_name
                group.invite_only = record.groups_invite_only
                group.url = record.groups_url
                group.creation = record.groups_creation
                group.irc_network = record.groups_irc_network
                group.needs_sponsor = record.groups_needs_sponsor
                group.prerequisite_id = record.groups_prerequisite_id
                group.user_can_remove = record.groups_user_can_remove
                group.mailing_list_url = record.groups_mailing_list_url
                group.mailing_list = record.groups_mailing_list
                group.irc_channel = record.groups_irc_channel
                group.apply_rules = record.groups_apply_rules
                group.joinmsg = record.groups_joinmsg
                group.group_type = record.groups_group_type
                group.owner_id = record.groups_owner_id
                group_map[record.groups_name] = group
            else:
                group = group_map[record.groups_name]

            if group.name not in person.group_roles:
                # Add the group to the person record
                person.memberships.append(group)

                role = Bunch()
                role.internal_comments = record.person_roles_internal_comments
                role.role_status = record.person_roles_role_status
                role.creation = record.person_roles_creation
                role.sponsor_id = record.person_roles_sponsor_id
                role.person_id = record.person_roles_person_id
                role.approval = record.person_roles_approval
                role.group_id = record.person_roles_group_id
                role.role_type = record.person_roles_role_type
                person.group_roles[group.name] = role
                person.roles.append(role)

        approved = []
        unapproved = []
        cla_done_group = config.get('cla_done_group', 'cla_done')
        for person in people_map.itervalues():
            if cla_done_group in person.group_roles:
                cla_status = person.group_roles[cla_done_group].role_status
            else:
                cla_status = 'unapproved'

            # Current default is to return everything unless fields is set
            if fields:
                # If set, return only the fields that were requested
                try:
                    person = dict((field, getattr(person, field)) for field
                            in fields)
                except AttributeError, error:
                    # An invalid field was given
                    turbogears.flash(_('Invalid field specified: %(error)s') %
                            {'error': str(error)})
                    if request_format() == 'json':
                        return dict(exc='Invalid', tg_template='json')
                    else:
                        return dict(people=[], unapproved_people=[],
                                search=search)

            if cla_status == 'approved':
                approved.append(person)
            else:
                unapproved.append(person)

        if not (approved or unapproved):
            turbogears.flash(_("No users found matching '%s'") % search)

        return dict(people=approved, unapproved_people=unapproved,
                search=search)

    @identity.require(identity.not_anonymous())
    @expose(format='json')
    def email_list(self, search=u'*'):
        '''Return a username to email address mapping.

        Keyword arguments:
        :search: filter the results by this search string.  * is a wildcard and
            the filter is anchored to the beginning of the username by default.

        Returns: a mapping of usernames to email addresses.  Note that users
            of all statuses, including bot, inactive, expired, and
            admin_disabled are included in this mapping.
        '''
        ### FIXME: Should port this to a validator
        # Work around a bug in TG (1.0.4.3-2)
        # When called as /user/list/*  search is a str type.
        # When called as /user/list/?search=* search is a unicode type.
        if not isinstance(search, unicode) and isinstance(search, basestring):
            search = unicode(search, 'utf-8', 'replace')

        re_search = search.translate({ord(u'*'): ur'%'}).lower()

        people = select([PeopleTable.c.username,
            PeopleTable.c.email]).where(People.username.like(
                re_search)).order_by('username').execute().fetchall()

        emails = dict(people)

        return dict(emails=emails)

    @identity.require(identity.not_anonymous())
    @expose(template='fas.templates.user.verifyemail')
    def verifyemail(self, token, cancel=False):
        ''' Used to verify the email address after a user has changed it

        :arg token: Token emailed to the user, if correct the email is verified
        :arg cancel: Cancel the outstanding change request
        :returns: person and token
        '''
        username = identity.current.user_name
        person = People.by_username(username)
        if cancel:
            person.emailtoken = ''
            turbogears.flash(_('Your pending email change has been canceled.'+\
            '   The email change token has been invalidated.'))
            turbogears.redirect('/user/view/%s' % username)
            return dict()
        if not person.unverified_email:
            turbogears.flash(_('You do not have any pending email changes.'))
            turbogears.redirect('/user/view/%s' % username)
            return dict()
        if person.emailtoken and (person.emailtoken != token):
            turbogears.flash(_('Invalid email change token.'))
            turbogears.redirect('/user/view/%s' % username)
            return dict()

        person = person.filter_private()
        return dict(person=person, token=token)

    @identity.require(identity.not_anonymous())
    @expose()
    def setemail(self, token):
        ''' Set email address once a request has been made

            :arg token: Token of change request
            :returns: Empty dict
        '''
        username = identity.current.user_name
        person = People.by_username(username)
        if not (person.unverified_email and person.emailtoken):
            turbogears.flash(_('You do not have any pending email changes.'))
            turbogears.redirect('/user/view/%s' % username)
            return dict()
        if person.emailtoken != token:
            turbogears.flash(_('Invalid email change token.'))
            turbogears.redirect('/user/view/%s' % username)
            return dict()
        # Log the change
        old_email = person.email
        person.email = person.unverified_email
        Log(author_id=person.id, description='Email changed from %s to %s' %
            (old_email, person.email))
        person.unverified_email = ''
        session.flush()
        turbogears.flash(_('You have successfully changed your email to \'%s\''
            ) % person.email)
        fas.fedmsgshim.send_message(topic="user.update", msg={
            'agent': person.username,
            'user': person.username,
            'fields': ('email',),
        })
        turbogears.redirect('/user/view/%s' % username)
        return dict()

    @expose(template='fas.templates.user.new')
    def new(self):
        ''' Displays the user with a form to to fill out to to sign up

        :returns: Captcha object and show
        '''

        show = {}
        show['show_postal_address'] = config.get('show_postal_address')
        if identity.not_anonymous():
            turbogears.flash(_('No need to sign up, you have an account!'))
            turbogears.redirect('/user/view/%s' % identity.current.user_name)
        return dict(captcha=CAPTCHA, show=show)

    @expose(template='fas.templates.new')
    @validate(validators=UserCreate())
    @error_handler(error) # pylint: disable-msg=E0602
    def create(self, username, human_name, email, verify_email, security_question, security_answer, telephone=None,
               postal_address=None, age_check=False, captcha=None, human_name_override=False):
        ''' Parse arguments from the UI and make sure everything is in order.

            :arg username: requested username
            :arg human_name: full name of new user
            :arg human_name_override: override check of user's full name
            :arg email: email address of the new user
            :arg verify_email: double check of users email
            :arg security_question: the security question in case user loses access to email
            :arg security_answer: the answer to the security question
            :arg telephone: telephone number of new user
            :arg postal_address: Mailing address of user
            :arg age_check: verifies user is over 13 years old
            :arg captcha: captcha to ensure the user is a human
            :returns: person

        '''
        # TODO: perhaps implement a timeout- delete account
        #           if the e-mail is not verified (i.e. the person changes
        #           their password) within X days.

        # Check that the user claims to be over 13 otherwise it puts us in a
        # legally sticky situation.
        if not age_check:
            turbogears.flash(_("We're sorry but out of special concern " +    \
            "for children's privacy, we do not knowingly accept online " +    \
            "personal information from children under the age of 13. We " +   \
            "do not knowingly allow children under the age of 13 to become " +\
            "registered members of our sites or buy products and services " + \
            "on our sites. We do not knowingly collect or solicit personal " +\
            "information about children under 13."))
            turbogears.redirect('/')
        email_test = select([PeopleTable.c.username],
                      func.lower(PeopleTable.c.email)==email.lower())\
                    .execute().fetchall()
        if email_test:
            turbogears.flash(_("Sorry.  That email address is already in " + \
                "use. Perhaps you forgot your password?"))
            turbogears.redirect("/")
            return dict()

        if email != verify_email:
            turbogears.flash(_("Sorry.  Email addresses do not match"))
            turbogears.redirect("/")
            return dict()
        try:
            person = self.create_user(username, human_name, email, security_question, security_answer,
                    telephone, postal_address, age_check)
        except IntegrityError:
            turbogears.flash(_("Your account could not be created.  Please " + \
                "contact %s for assistance.") % config.get('accounts_email'))
            turbogears.redirect('/user/new')
            return dict()
        else:
            Log(author_id=person.id, description='Account created: %s' %
                person.username)
            turbogears.flash(_('Your password has been emailed to you.  ' + \
                'Please log in with it and change your password'))
            turbogears.redirect('/user/changepass')
            return dict()

    def create_user(self, username, human_name, email, security_question, security_answer,
        telephone=None, postal_address=None, age_check=False, redirect_location='/'):
        ''' create_user: saves user information to the database and sends a
            welcome email.

            :arg username: requested username
            :arg human_name: full name of new user
            :arg email: email address of the new user
            :arg security_question: the question to identify the user when he loses access to his email
            :arg security_answer: the answer to the security question
            :arg telephone: telephone number of new user
            :arg postal_address: Mailing address of user
            :arg age_check: verifies user is over 13 years old
            :arg redirect: location to redirect to after creation
            :returns: person
        '''
        # Check that the user claims to be over 13 otherwise it puts us in a
        # legally sticky situation.
        if not age_check:
            turbogears.flash(_("We're sorry but out of special concern " +    \
            "for children's privacy, we do not knowingly accept online " +    \
            "personal information from children under the age of 13. We " +   \
            "do not knowingly allow children under the age of 13 to become " +\
            "registered members of our sites or buy products and services " + \
            "on our sites. We do not knowingly collect or solicit personal " +\
            "information about children under 13."))
            turbogears.redirect(redirect_location)
        test = select([PeopleTable.c.username],
            func.lower(PeopleTable.c.email)==email.lower()).execute().fetchall()
        if test:
            turbogears.flash(_("Sorry.  That email address is already in " + \
                "use. Perhaps you forgot your password?"))
            turbogears.redirect(redirect_location)
            return dict()
        person = People()
        person.username = username
        person.human_name = human_name
        person.telephone = telephone
        person.postal_address = postal_address
        person.email = email
        person.security_question = security_question
        person.security_answer = encrypt_text(config.get('key_securityquestion'), security_answer)
        person.password = '*'
        person.status = 'active'
        person.old_password = generate_password()['hash']
        session.flush()
        newpass = generate_password()
        send_mail(person.email, _('Welcome to the Fedora Project!'), _('''
You have created a new Fedora account!
Your username is: %(username)s
Your new password is: %(password)s

Please go to %(base_url)s%(webpath)s/user/changepass
to change it.

Welcome to the Fedora Project. Now that you've signed up for an
account you're probably desperate to start contributing, and with that
in mind we hope this e-mail might guide you in the right direction to
make this process as easy as possible.

Fedora is an exciting project with lots going on, and you can
contribute in a huge number of ways, using all sorts of different
skill sets. To find out about the different ways you can contribute to
Fedora, you can visit our join page which provides more information
about all the different roles we have available.

http://join.fedoraproject.org/

If you already know how you want to contribute to Fedora, and have
found the group already working in the area you're interested in, then
there are a few more steps for you to get going.

Foremost amongst these is to sign up for the team or project's mailing
list that you're interested in - and if you're interested in more than
one group's work, feel free to sign up for as many mailing lists as
you like! This is because mailing lists are where the majority of work
gets organised and tasks assigned, so to stay in the loop be sure to
keep up with the messages.

Once this is done, it's probably wise to send a short introduction to
the list letting them know what experience you have and how you'd like
to help. From here, existing members of the team will help you to find
your feet as a Fedora contributor.

Please remember that you are joining a community made of contributors
from all around the world, as such please stop by the Community Code of
Conduct.

https://fedoraproject.org/code-of-conduct

And finally, from all of us here at the Fedora Project, we're looking
forward to working with you!
''') % {'username': person.username,
        'password': newpass['pass'],
        'base_url': config.get('base_url_filter.base_url'),
        'webpath': config.get('server.webpath')})
        person.password = newpass['hash']
        fas.fedmsgshim.send_message(topic="user.create", msg={
            'agent': person.username,
            'user': person.username,
        })
        return person

    @identity.require(identity.not_anonymous())
    @expose(template="fas.templates.user.changequestion")
    def changequestion(self):
        ''' Provides forms for user to change security question/answer

        :rerturns: empty dict
        '''
        return dict()

    @identity.require(identity.not_anonymous())
    @validate(validators=UserSetSecurityQuestion())
    @error_handler(error)
    @expose(template="fas.templates.user.changequestion")
    def setquestion(self, currentpassword, newquestion, newanswer):
        username = identity.current.user_name
        person = People.by_username(username)

        # These are done here instead of in the validator because we may not
        # have access to identity when testing the validators
        if not person.password == crypt.crypt(currentpassword.encode('utf-8'),
                person.password):
            turbogears.flash(_('Your current password did not match'))
            return dict()

        try:
            person.security_question = newquestion
            person.security_answer = encrypt_text(config.get('key_securityquestion'), newanswer)
            Log(author_id=person.id, description='Security question changed')
            session.flush()
        # TODO: Make this catch something specific.
        except:
            Log(author_id=person.id, description='Security question change failed!')
            turbogears.flash(_("Your security question could not be changed."))
            return dict()
        else:
            turbogears.flash(_("Your security question has been changed."))
            fas.fedmsgshim.send_message(topic="user.update", msg={
                'agent': person.username,
                'user': person.username,
                'fields': ['security_question', 'security_answer'],
            })
            turbogears.redirect('/user/view/%s' % identity.current.user_name)
            return dict()

    @identity.require(identity.not_anonymous())
    @expose(template="fas.templates.user.changepass")
    def changepass(self):
        ''' Provides forms for user to change password

        :returns: empty dict
        '''
        return dict()

    @identity.require(identity.not_anonymous())
    @validate(validators=UserSetPassword())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.changepass")
    def setpass(self, currentpassword, password, passwordcheck):
        username = identity.current.user_name
        person  = People.by_username(username)

        # This is here due to a bug in older formencode where
        # ChainedValidators did not fire
        if password != passwordcheck:
            turbogears.flash(_('passwords did not match'))
            return dict()

        # These are done here instead of in the validator because we may not
        # have access to identity when testing the validators
        if not person.password == crypt.crypt(currentpassword.encode('utf-8'),
                person.password):
            turbogears.flash(_('Your current password did not match'))
            return dict()

        if currentpassword == password:
            turbogears.flash(_(
                'Your new password cannot be the same as your old one.'))
            return dict()

        newpass = generate_password(password)

        try:
            person.old_password = person.password
            person.password = newpass['hash']
            person.password_changed = datetime.now(pytz.utc)
            Log(author_id=person.id, description='Password changed')
            session.flush()
        # TODO: Make this catch something specific.
        except:
            Log(author_id=person.id, description='Password change failed!')
            turbogears.flash(_("Your password could not be changed."))
            return dict()
        else:
            turbogears.flash(_("Your password has been changed."))
            fas.fedmsgshim.send_message(topic="user.update", msg={
                'agent': person.username,
                'user': person.username,
                'fields': ['password'],
            })
            turbogears.redirect('/user/view/%s' % identity.current.user_name)
            return dict()

    @expose(template="fas.templates.user.resetpass")
    def resetpass(self):
        ''' Prompt user to reset password

        :returns: empty dict
        '''
        if identity.not_anonymous():
            turbogears.flash(_('You are already logged in!'))
            turbogears.redirect('/user/view/%s' % identity.current.user_name)
        return dict()

    @expose(template="fas.templates.user.resetpass")
    def sendtoken(self, username, email, encrypted=False):
        ''' Email token to user for password reset

        :arg username: username of user for verification
        :arg email: email of user for verification
        :arg encrypted: Should we encrypt the password
        :returns: empty dict
        '''
        # Candidate for a validator later
        username = username.lower()
        email = email.lower()
        if identity.current.user_name:
            turbogears.flash(_("You are already logged in."))
            turbogears.redirect('/user/view/%s' % identity.current.user_name)
            return dict()
        try:
            person = People.by_username(username)
        except InvalidRequestError:
            turbogears.flash(_('Username email combo does not exist!'))
            turbogears.redirect('/user/resetpass')

        if email != person.email.lower():
            turbogears.flash(_("username + email combo unknown."))
            return dict()
        if person.status in ('expired', 'admin_disabled'):
            turbogears.flash(_("Your account currently has status " + \
                "%(status)s.  For more information, please contact " + \
                "%(admin_email)s") % \
                {'status': person.status,
                    'admin_email': config.get('accounts_email')})
            return dict()
        if person.status == ('bot'):
            turbogears.flash(_('System accounts cannot have their ' + \
                'passwords reset online.  Please contact %(admin_email)s ' + \
                'to have it reset') % \
                    {'admin_email': config.get('accounts_email')})
            reset_subject = _('Warning: attempted reset of system account')
            reset_text = _('''
Warning: Someone attempted to reset the password for system account
%(account)s via the web interface.
''') % {'account': username}
            send_mail(config.get('accounts_email'), reset_subject, reset_text)
            return dict()

        token_charset = string.ascii_letters + string.digits
        token = random_string(token_charset, 32)
        mail = _('''
Somebody (hopefully you) has requested a password reset for your account!
To change your password (or to cancel the request), please visit

%(verifyurl)s/accounts/user/verifypass/%(user)s/%(token)s
''') % {'verifyurl' : config.get('base_url_filter.base_url').rstrip('/'),
        'user': username, 'token': token}
        if encrypted:
            # TODO: Move this out to mail function
            # think of how to make sure this doesn't get
            # full of random keys (keep a clean Fedora keyring)
            # TODO: MIME stuff?
            keyid = re.sub('\s', '', person.gpg_keyid)
            if not keyid:
                turbogears.flash(_("This user does not have a GPG Key ID " +\
                    "set, so an encrypted email cannot be sent."))
                return dict()
            ret = subprocess.call([config.get('gpgexec'), '--keyserver',
                config.get('gpg_keyserver'), '--recv-keys', keyid])
            if ret != 0:
                turbogears.flash(_(
                    "Your key could not be retrieved from subkeys.pgp.net"))
                turbogears.redirect('/user/resetpass')
                return dict()
            else:
                try:
                    # This may not be the neatest fix, but gpgme gave an error
                    # when mail was unicode.
                    plaintext = StringIO.StringIO(mail.encode('utf-8'))
                    ciphertext = StringIO.StringIO()
                    ctx = gpgme.Context()
                    ctx.armor = True
                    signer = ctx.get_key(re.sub('\s', '',
                        config.get('gpg_fingerprint')))
                    ctx.signers = [signer]
                    recipient = ctx.get_key(keyid)
                    def passphrase_cb(uid_hint, passphrase_info,
                            prev_was_bad, file_d):
                        ''' Get gpg passphrase '''
                        os.write(file_d, '%s\n' % config.get('gpg_passphrase'))
                    ctx.passphrase_cb = passphrase_cb
                    ctx.encrypt_sign([recipient],
                        gpgme.ENCRYPT_ALWAYS_TRUST,
                        plaintext,
                        ciphertext)
                    mail = ciphertext.getvalue()
                except:
                    turbogears.flash(_(
                        'Your password reset email could not be encrypted.'))
                    return dict()
        send_mail(email, _('Fedora Project Password Reset'), mail)
        person.passwordtoken = token
        Log(author_id=person.id,
            description='Password reset sent for %s' % person.username)
        turbogears.flash(_('A password reset URL has been emailed to you.'))
        turbogears.redirect('/login')
        return dict()

    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.verifypass")
    @validate(validators={'username' : KnownUser})
    def verifypass(self, username, token, cancel=False):
        ''' Verifies whether or not the user has a password change request

            :arg username: username of person to password change
            :arg token: Token to check
            :arg cancel: Whether or not to cancel the request
            :returns: empty dict
        '''

        person = People.by_username(username)
        if person.status in ('expired', 'admin_disabled'):
            turbogears.flash(_("Your account currently has status " + \
                "%(status)s.  For more information, please contact " + \
                "%(admin_email)s") % {'status': person.status,
                 'admin_email': config.get('accounts_email')})
            return dict()
        if not person.passwordtoken:
            turbogears.flash(_("You don't have any pending password changes."))
            turbogears.redirect('/login')
            return dict()
        if person.passwordtoken != token:
            turbogears.flash(_('Invalid password change token.'))
            turbogears.redirect('/login')
            return dict()
        if cancel:
            person.passwordtoken = ''
            Log(author_id=person.id,
                description='Password reset cancelled for %s' %
                person.username)
            turbogears.flash(_('Your password reset has been canceled.  ' + \
                'The password change token has been invalidated.'))
            turbogears.redirect('/login')
            return dict()
        person = person.filter_private()
        return dict(person=person, token=token)

    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.verifypass")
    @validate(validators=UserResetPassword())
    def setnewpass(self, username, token, password, passwordcheck):
        ''' Sets a new password for a user

        :arg username: Username of user to change password
        :arg token: sanity check token
        :arg password: new plain text password
        :arg passwordcheck: must match password

        :returns: empty dict or error
        '''
        person = People.by_username(username)
        changed = []  # Field names updated to emit via fedmsg

        # Note: the following check should be done by the validator.  It's
        # here because of a bug in older formencode that caused chained
        # validators to not fire.
        if password != passwordcheck:
            turbogears.flash(_("Both passwords must match"))
            return dict()

        if person.status in ('expired', 'admin_disabled'):
            turbogears.flash(_("Your account currently has status " + \
                "%(status)s.  For more information, please contact " + \
                "%(admin_email)s") % \
                {'status': person.status,
                    'admin_email': config.get('accounts_email')})
            return dict()

        if not person.passwordtoken:
            turbogears.flash(_('You do not have any pending password changes.'))
            turbogears.redirect('/login')
            return dict()

        if person.passwordtoken != token:
            person.emailtoken = ''
            turbogears.flash(_('Invalid password change token.'))
            turbogears.redirect('/login')
            return dict()

        # Re-enabled!
        if person.status in ('inactive'):
            # Check that the password has changed.
            if (person.old_password and
                    crypt.crypt(password.encode('utf-8'), person.old_password)
                        == person.old_password) or (
                    person.password and
                    self.crypted_password_re.match(person.password) and
                    crypt.crypt(password.encode('utf-8'), person.password)
                        == person.password):
                turbogears.flash(_('Your password can not be the same ' + \
                        'as your old password.'))
                return dict(person=person, token=token)

            person.status = 'active'
            person.status_change = datetime.now(pytz.utc)
            changed.append('status')

        # Log the change
        newpass = generate_password(password)
        person.old_password = person.password
        person.password = newpass['hash']
        person.password_changed = datetime.now(pytz.utc)
        person.passwordtoken = ''
        changed.append('password')
        Log(author_id=person.id, description='Password changed')
        session.flush()

        turbogears.flash(_('You have successfully reset your password.  ' + \
            'You should now be able to login below.'))
        fas.fedmsgshim.send_message(topic="user.update", msg={
            'agent': person.username,
            'user': person.username,
            'fields': changed,
        })
        turbogears.redirect('/login')
        return dict()

    @identity.require(identity.not_anonymous())
    @expose(template="fas.templates.user.gencert")
    def gencert(self):
        ''' Displays a simple text link to users to click to actually get a
            certificate

        :returns: empty dict
        '''
        return dict()

    @identity.require(identity.not_anonymous())
    @expose(template="genshi:fas.templates.user.gencertdisabled",
        allow_json=True, content_type='text/html')
    @expose(template="genshi-text:fas.templates.user.cert", format="text",
        content_type='application/x-x509-user-cert', allow_json=True)
    def dogencert(self):
        ''' Generates a user certificate

        :returns: empty dict though via tg it returns an x509 cert'''
        from cherrypy import response
        if not config.get('gencert', False):
            # Certificate generation is disabled on this machine
            # Return the error page
            return dict()
        import tempfile
        username = identity.current.user_name
        person = People.by_username(username)
        if not cla_done(person):
            if self.json_request():
                return dict(cla=False)
            turbogears.flash(_('Before generating a certificate, you must ' + \
                'first complete the FPCA.'))
            turbogears.redirect('/fpca/')
            return dict()

        response.headers["content-disposition"] = "attachment"
        pkey = openssl_fas.createKeyPair(openssl_fas.TYPE_RSA, 2048)

        digest = config.get('openssl_digest')

        req = openssl_fas.createCertRequest(pkey, digest=digest,
            C=config.get('openssl_c'),
            ST=config.get('openssl_st'),
            L=config.get('openssl_l'),
            O=config.get('openssl_o'),
            OU=config.get('openssl_ou'),
            CN=person.username,
            emailAddress=person.email,
        )

        reqdump = crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)
        certdump = ''

        while True:
            try:
                os.mkdir(os.path.join(config.get('openssl_lockdir'), 'lock'))
                break
            except OSError:
                time.sleep(0.75)

        try:
            reqfile = tempfile.NamedTemporaryFile()
            reqfile.write(reqdump)
            reqfile.flush()

            indexfile = open(config.get('openssl_ca_index'))
            for entry in indexfile:
                attrs = entry.split('\t')
                if attrs[0] != 'V':
                    continue
                # the index line looks something like this:
                # R\t090816180424Z\t080816190734Z\t01\tunknown\t/C=US/ST=Pennsylvania/O=Fedora/CN=test1/emailAddress=rickyz@cmu.edu
                # V\t090818174940Z\t\t01\tunknown\t/C=US/ST=North Carolina/O=Fedora Project/OU=Upload Files/CN=toshio/emailAddress=badger@clingman.lan
                distinguished_name = attrs[5]
                serial = attrs[3]
                info = {}
                for pair in distinguished_name.split('/'):
                    if pair:
                        key, value = pair.split('=')
                        info[key] = value
                if info['CN'] == person.username:
                    # revoke old certs
                    subprocess.call([config.get('makeexec'), '-C',
                        config.get('openssl_ca_dir'), 'revoke',
                        'cert=%s/%s' % (config.get('openssl_ca_newcerts'),
                        serial + '.pem')])

            certfile = tempfile.NamedTemporaryFile()
            command = [config.get('makeexec'), '-C',
                    config.get('openssl_ca_dir'), 'sign',
                    'req=%s' % reqfile.name, 'cert=%s' % certfile.name]
            ret = subprocess.call(command)
            reqfile.close()

            certdump = certfile.read()
            certfile.close()
        finally:
            os.rmdir(os.path.join(config.get('openssl_lockdir'), 'lock'))

        if ret != 0:
            turbogears.flash(_('Your certificate could not be generated.'))
            turbogears.redirect('/home')
            return dict()
        keydump = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
        cherrypy.request.headers['Accept'] = 'text'

        gencert_subject = _('A new certificate has been generated for %s') % \
            person.username
        gencert_text = _('''
You have generated a new SSL certificate.  If you did not request this,
please cc admin@fedoraproject.org and let them know.

Note that certificates generated prior to the current one have been
automatically revoked, and should stop working within the hour.
''')
        send_mail(person.email, gencert_subject, gencert_text)
        Log(author_id=person.id, description='Certificate generated for %s' %
            person.username)
        fas.fedmsgshim.send_message(topic="user.update", msg={
            'agent': person.username,
            'user': person.username,
            'fields': 'certificate',
        })
        return dict(tg_template="genshi-text:fas.templates.user.cert",
                cla=True, cert=certdump, key=keydump)

    @identity.require(identity.in_group(
                        config.get('systemgroup', 'fas-system')))
    @expose(allow_json=True)
    def update_last_seen(self, username, last_seen=None):
        ''' Update the persons last_seen field in the database

        :arg username: Username of the person to update
        :arg last_seen: Specify the time they were last seen, else now
                        Format should be string: YYYY,MM,DD,hh,mm,ss
        :returns: Empty dict on success
        '''

        if not last_seen:
            last_seen = datetime.now(pytz.utc)
        else:
            update_time = last_seen.split(',')
            last_seen = datetime(int(update_time[0]),   # Year
                                int(update_time[1]),    # Month
                                int(update_time[2]),    # Day
                                int(update_time[3]),    # Hour
                                int(update_time[4]),    # Minute
                                int(update_time[5]),    # Second
                                0,                      # ms
                                pytz.utc)               # tz
        person = People.by_username(username)
        print "LAST_SEEN: %s" % last_seen
        person.last_seen = last_seen
        session.flush()
        return dict()

    @identity.require(identity.not_anonymous())
    @expose()
    def clearkey(self):
        username = identity.current.user_name
        person  = People.by_username(username)
        person.ssh_key = ''
        fas.fedmsgshim.send_message(topic="user.update", msg={
            'agent': person.username,
            'user': person.username,
            'fields': ['ssh_key'],
        })
        turbogears.flash(_('Your key has been removed.'))
        turbogears.redirect('/user/view/%s' % username)
        return dict()
