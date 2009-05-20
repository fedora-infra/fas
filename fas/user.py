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

# @error_handler() takes a reference to the error() method defined in the
# class (E0602)

import turbogears
from turbogears import controllers, expose, identity, \
        validate, validators, error_handler, config
from turbogears.database import session
import cherrypy

from fas.util import send_mail

import os
import re
import gpgme
import StringIO
import crypt
import random
import subprocess
from OpenSSL import crypto

import pytz
from datetime import datetime
import time

from sqlalchemy import func
from sqlalchemy.exceptions import IntegrityError, InvalidRequestError
from sqlalchemy.sql import select, and_, not_

from fedora.tg.util import request_format

import fas
from fas.model import PeopleTable, PersonRolesTable, GroupsTable
from fas.model import People, PersonRoles, Groups, Log
from fas import openssl_fas
from fas.auth import isAdmin, CLADone, canEditUser
from fas.util import available_languages
from fas.validators import KnownUser, ValidSSHKey, NonFedoraEmail, \
        ValidLanguage, UnknownUser, ValidUsername

admin_group = config.get('admingroup', 'accounts')
system_group = config.get('systemgroup', 'fas-system')
thirdparty_group = config.get('thirdpartygroup', 'thirdparty')

class UserView(validators.Schema):
    username = KnownUser

class UserEdit(validators.Schema):
    targetname = KnownUser

class UserSave(validators.Schema):
    targetname = KnownUser
    human_name = validators.All(
        validators.String(not_empty=True, max=42),
        validators.Regex(regex='^[^\n:<>]+$'),
        )
    status = validators.OneOf(['active', 'inactive', 'expired', 'admin_disabled'])
    ssh_key = ValidSSHKey(max=5000)
    email = validators.All(
        validators.Email(not_empty=True, strip=True, max=128),
        NonFedoraEmail(not_empty=True, strip=True, max=128),
    )
    locale = ValidLanguage(not_empty=True, strip=True)
    #fedoraPersonBugzillaMail = validators.Email(strip=True, max=128)
    #fedoraPersonKeyId- Save this one for later :)
    postal_address = validators.String(max=512)
    country_code = validators.String(max=2, strip=True)
    privacy = validators.Bool
    latitude = validators.Number
    longitude = validators.Number

class UserCreate(validators.Schema):
    username = validators.All(
        UnknownUser,
        ValidUsername(not_empty=True),
        validators.String(max=32, min=3),
    )
    human_name = validators.All(
        validators.String(not_empty=True, max=42),
        validators.Regex(regex='^[^\n:<>]+$'),
        )
    email = validators.All(
        validators.Email(not_empty=True, strip=True),
        NonFedoraEmail(not_empty=True, strip=True),
    )
    #fedoraPersonBugzillaMail = validators.Email(strip=True)
    postal_address = validators.String(max=512)

class UserSetPassword(validators.Schema):
    currentpassword = validators.String
    # TODO (after we're done with most testing): Add complexity requirements?
    password = validators.String(min=8)
    passwordcheck = validators.String
    chained_validators = [validators.FieldsMatch('password', 'passwordcheck')]

class VerifyPass(validators.Schema):
    username = KnownUser

class UserResetPassword(validators.Schema):
    # TODO (after we're done with most testing): Add complexity requirements?
    password = validators.String(min=8)
    passwordcheck = validators.String
    chained_validators = [validators.FieldsMatch('password', 'passwordcheck')]

### FIXME: If not going to be used, delete
#class SendToken(validators.Schema):
#    username = KnownUser

def generate_password(password=None, length=16):
    ''' Generate Password '''
    secret = {} # contains both hash and password

    if not password:
        # Exclude 1,l and 0,O
        chars = '23456789abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNPQRSTUVWXYZ'
        password = ''
        # char_num is just a counter for the loop (W0612)
        for char_num in xrange(length): # pylint: disable-msg=W0612
            password += random.choice(chars)

    secret['hash'] = crypt.crypt(password.encode('utf-8'), "$1$%s" % generate_salt(8))
    secret['pass'] = password

    return secret

def generate_salt(length=8):
    chars = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    salt = ''
    # char_num is just a counter for the loop (W0612)
    for char_num in xrange(length): # pylint: disable-msg=W0612
        salt += random.choice(chars)
    return salt

def generate_token(length=32):
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    token = ''
    # char_num is just a counter for the loop (W0612)
    for char_num in xrange(length): # pylint: disable-msg=W0612
        token += random.choice(chars)
    return token

class User(controllers.Controller):

    def __init__(self):
        '''Create a User Controller.
        '''

    @identity.require(identity.not_anonymous())
    def index(self):
        '''Redirect to view
        '''
        turbogears.redirect('/user/view/%s' % identity.current.user_name)

    def jsonRequest(self):
        return 'tg_format' in cherrypy.request.params and \
                cherrypy.request.params['tg_format'] == 'json'


    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(identity.not_anonymous())
    @validate(validators=UserView())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.view", allow_json=True)
    def view(self, username=None):
        '''View a User.
        '''
        if not username:
            username = identity.current.user_name
        person = People.by_username(username)
        if identity.current.user_name == username:
            personal = True
        else:
            personal = False
        # TODO: We can do this without a db lookup by using something like
        # if groupname in identity.groups: pass
        # We may want to do that in isAdmin() though. -Toshio
        user = People.by_username(identity.current.user_name)
        admin = False
        if isAdmin(user):
            admin = True
            # TODO: Should admins be able to see personal info?  If so, enable this.  
            # Either way, let's enable this after the testing period.
            # 
            # 2008-5-14 I'd enable this in the template via
            # <py:if test='personal or admin'>click to change</py:if>
            # that way you can have different messages for an admin viewing
            # their own page via
            # <py:if test='personal'>My Account</py:if>
            # <py:if test="not personal">${user}'s Account</py:if>
            # -Toshio
            #personal = True
        cla = CLADone(person)
        person.filter_private()
        person.json_props = {
                'People': ('approved_memberships', 'unapproved_memberships')
                }
        return dict(person=person, cla=cla, personal=personal, admin=admin)

    @identity.require(identity.not_anonymous())
    @validate(validators=UserEdit())
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

        admin = isAdmin(person)

        if targetname:
            target = People.by_username(targetname)
        else:
            target = person

        if not canEditUser(person, target):
            turbogears.flash(_('You cannot edit %s') % target.username)
            turbogears.redirect('/user/view/%s' % target.username)
            return dict()

        target.filter_private()
        return dict(target=target, languages=languages, admin=admin, show=show)

    @identity.require(identity.not_anonymous())
    @validate(validators=UserSave())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.user.edit')
    def save(self, targetname, human_name, telephone, postal_address, 
             email, status, ssh_key=None, ircnick=None, gpg_keyid=None, 
             comments='', locale='en', timezone='UTC', country_code='',
             latitude=None, longitude=None, privacy=False):
        languages = available_languages()

        username = identity.current.user_name
        target = targetname
        person = People.by_username(username)
        target = People.by_username(target)
        emailflash = ''

        if not canEditUser(person, target):
            turbogears.flash(_("You do not have permission to edit '%s'") % target.username)
            turbogears.redirect('/user/view/%s', target.username)
            return dict()
        try:
            if target.status != status:
                if (status in ('expired', 'admin_disabled') or target.status in ('expired', 'admin_disabled')) and \
                    not isAdmin(person):
                    turbogears.flash(_('Only administrator can enable or disable an account.'))
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
                Log(author_id=person.id, description='%(person)s\'s status changed from %(old)s to %(new)s' % \
                    {'person': target.username,
                     'old': target.status,
                     'new': status})
                target.status = status
                target.status_change = datetime.now(pytz.utc)
            target.human_name = human_name
            if target.email != email:
                test = select([PeopleTable.c.username], func.lower(PeopleTable.c.email)==email.lower()).execute().fetchall()
                if test:
                    turbogears.flash(_('Somebody is already using that email address.'))
                    turbogears.redirect("/user/edit/%s" % target.username)
                    return dict()
                emailflash = _('Before your new email takes effect, you must confirm it.  You should receive an email with instructions shortly.')
                token = generate_token()
                target.unverified_email = email
                target.emailtoken = token
                change_subject = _('Email Change Requested for %s') % person.username
                change_text = _('''
You have recently requested to change your Fedora Account System email
to this address.  To complete the email change, you must confirm your
ownership of this email by visiting the following URL (you will need to
login with your Fedora account first):

https://admin.fedoraproject.org/accounts/user/verifyemail/%s
''') % token
                send_mail(email, change_subject, change_text)
            target.ircnick = ircnick
            target.gpg_keyid = gpg_keyid
            target.telephone = telephone
            if ssh_key:
                target.ssh_key = ssh_key
            target.postal_address = postal_address
            target.comments = comments
            target.locale = locale
            target.timezone = timezone
            target.country_code = country_code
            target.latitude = latitude and float(latitude) or None
            target.longitude = longitude and float(longitude) or None
            target.privacy = privacy
#            target.set_share_cc(share_country_code)
#            target.set_share_loc(share_location)
        except TypeError, e:
            turbogears.flash(_('Your account details could not be saved: %s') % e)
            turbogears.redirect("/user/edit/%s" % target.username)
            return dict()
        else:
            change_subject = _('Fedora Account Data Update %s') % target.username
            change_text = '''
You have just updated information about your account.  If you did not request
these changes please contact admin@fedoraproject.org and let them know.  Your
update information is:

  username:       %(username)s
  ircnick:        %(ircnick)s
  telephone:      %(telephone)s
  locale:         %(locale)s
  postal_address: %(postal_address)s
  timezone:       %(timezone)s
  country code:   %(country_code)s
  latitude:       %(latitude)s
  longitude:      %(longitude)s
  privacy flag:   %(privacy)s
  ssh_key:        %(ssh_key)s

If the above information is incorrect, please log in and fix it:
https://admin.fedoraproject.org/accounts/user/edit/%(username)s
''' % { 'username'       : target.username,
         'ircnick'        : target.ircnick,
         'telephone'      : target.telephone,
         'locale'         : target.locale,
         'postal_address' : target.postal_address,
         'timezone'       : target.timezone,
         'country_code'   : target.country_code,
         'latitude'       : target.latitude,
         'longitude'      : target.longitude,
         'privacy'        : target.privacy,
         'ssh_key'        : target.ssh_key }
            send_mail(target.email, change_subject, change_text)
            turbogears.flash(_('Your account details have been saved.') + '  ' + emailflash)
            turbogears.redirect("/user/view/%s" % target.username)
            return dict()

    @identity.require(identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.list", allow_json=True)
    def dump(self, search=u'a*', groups=''):
        
        groups_to_return_list = groups.split(',')
        groups_to_return = []
        # Special Logic, find out all the people who are in more then one group
        if '@all' in groups_to_return_list:
            g = Groups.query().filter(not_(Groups.name.ilike('cla%')))
            for group in g:
                groups_to_return.append(group.name)
        
        for group_type in groups_to_return_list:
            if group_type.startswith('@'):
                group_list = Groups.query.filter(Groups.c.group_type.in_([group_type.strip('@')]))
                for group in group_list:
                    groups_to_return.append(group.name)
            else:
                groups_to_return.append(group_type)
        people = People.query.join('roles').filter(PersonRoles.role_status=='approved').join(PersonRoles.group).filter(Groups.c.name.in_( groups_to_return ))
        
        # p becomes what we send back via json
        p = []
        for strip_p in people:
            strip_p.filter_private()
            if strip_p.status == 'active':
                p.append({
                    'username'  : strip_p.username,
                    'id'        : strip_p.id,
                    'ssh_key'   : strip_p.ssh_key,
                    'human_name': strip_p.human_name,
                    'password'  : strip_p.password 
                    })

        return dict(people=p, unapproved_people=[], search=search)

    @identity.require(identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.list", allow_json=True)
    def list(self, search=u'a*', fields=None):
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

        # Query db for all users and their status in cla_done
        RoleGroupJoin = PersonRolesTable.join(GroupsTable,
                and_(PersonRoles.group_id==Groups.id, Groups.name=='cla_done'))
        PeopleJoin = PeopleTable.outerjoin(RoleGroupJoin,
                PersonRoles.person_id==People.id)

        stmt = select([PeopleTable, PersonRolesTable.c.role_status],
                from_obj=[PeopleJoin]).where(People.username.ilike(re_search)
                          ).order_by(People.username)
        people = People.query.add_column(PersonRoles.role_status
                ).from_statement(stmt)

        approved = []
        unapproved = []
        for person in people.all():
            person[0].filter_private()
            # Current default is to return everything unless fields is set
            if fields:
                # If set, return only the fields that were requested
                try:
                    user = dict((field, getattr(person[0], field)) for field
                            in fields)
                except AttributeError, e:
                    # An invalid field was given
                    turbogears.flash(_('Invalid field specified: %(error)s') %
                            {'error': str(e)})
                    if request_format() == 'json':
                        return dict(exc='Invalid', tg_template='json')
                    else:
                        return dict(people=[], unapproved_people=[],
                                search=search)
            else:
                user = person[0]

            if person[1] == 'approved':
                approved.append(user)
            else:
                unapproved.append(user)

        if not (approved or unapproved):
            turbogears.flash(_("No users found matching '%s'") % search)

        return dict(people=approved, unapproved_people=unapproved,
                search=search)

    @identity.require(identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(format='json')
    def email_list(self, search=u'*'):
        '''Return a username to email address mapping.

        Note: If the caller is not authorized to view the email address of a
        particular user, username@fedoraproject.org will be put there instead.
        These are typically email aliases to the user's email address but
        please be aware that the aliases only exist if the user is approved in
        at least one group (so not every username will have an email alias).

        Although this method checks that the person's status is active, it does
        not perform CLA or group checking.  Thus, the @fedoraproject.org email
        addresses that it returns are not guaranteed to exist.

        Keyword arguments:
        :search: filter the results by this search string.  * is a wildcard and
            the filter is anchored to the beginning of the username by default.

        Returns: a mapping of usernames to email addresses.
        '''
        ### FIXME: Should port this to a validator
        # Work around a bug in TG (1.0.4.3-2)
        # When called as /user/list/*  search is a str type.
        # When called as /user/list/?search=* search is a unicode type.
        if not isinstance(search, unicode) and isinstance(search, basestring):
            search = unicode(search, 'utf-8', 'replace')

        re_search = search.translate({ord(u'*'): ur'%'}).lower()
        people = People.query.filter(and_(People.username.like(re_search), People.status == 'active')).order_by('username')
        emails = {}
        # Run filter_private via side effect
        for person, discard in ((p, p.filter_private()) for p in people):
            emails[person.username] = person.email or '%s@fedoraproject.org' \
                    % person.username
        return dict(emails=emails)

    @identity.require(identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.user.verifyemail')
    def verifyemail(self, token, cancel=False):
        username = identity.current.user_name
        person = People.by_username(username)
        if cancel:
            person.emailtoken = ''
            turbogears.flash(_('Your pending email change has been canceled.  The email change token has been invalidated.'))
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

        person.filter_private()
        return dict(person=person, token=token)

    @identity.require(identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose()
    def setemail(self, token):
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
        ''' Log this '''
        oldEmail = person.email
        person.email = person.unverified_email
        Log(author_id=person.id, description='Email changed from %s to %s' % (oldEmail, person.email))
        person.unverified_email = ''
        session.flush()
        turbogears.flash(_('You have successfully changed your email to \'%s\'') % person.email)
        turbogears.redirect('/user/view/%s' % username)
        return dict()

    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.user.new')
    def new(self):
        if identity.not_anonymous():
            turbogears.flash(_('No need to sign up, you have an account!'))
            turbogears.redirect('/user/view/%s' % identity.current.user_name)
        return dict()

    @validate(validators=UserCreate())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template='fas.templates.new')
    def create(self, username, human_name, email, telephone=None, 
               postal_address=None, age_check=False):
        # TODO: perhaps implement a timeout- delete account
        #           if the e-mail is not verified (i.e. the person changes
        #           their password) withing X days.

        # Check that the user claims to be over 13 otherwise it puts us in a
        # legally sticky situation.
        if not age_check:
            turbogears.flash(_("We're sorry but out of special concern for children's privacy, we do not knowingly accept online personal information from children under the age of 13. We do not knowingly allow children under the age of 13 to become registered members of our sites or buy products and services on our sites. We do not knowingly collect or solicit personal information about children under 13."))
            turbogears.redirect('/')
        test = select([PeopleTable.c.username], 
                      func.lower(PeopleTable.c.email)==email.lower())\
                    .execute().fetchall()
        if test:
            turbogears.flash(_("Sorry.  That email address is already in use. Perhaps you forgot your password?"))
            turbogears.redirect("/")
            return dict()
        try:
            self.create_user(username, human_name, email, telephone, 
                             postal_address, age_check)
        except IntegrityError:
            turbogears.flash(_("Your account could not be created.  Please contact %s for assistance.") % config.get('accounts_email'))
            turbogears.redirect('/user/new')
            return dict()
        else:
            turbogears.flash(_('Your password has been emailed to you.  Please log in with it and change your password'))
            turbogears.redirect('/user/changepass')
            return dict()

    def create_user(self, username, human_name, email, telephone=None, postal_address=None, age_check=False, redirect='/'):
        # Check that the user claims to be over 13 otherwise it puts us in a
        # legally sticky situation.
        if not age_check:
            turbogears.flash(_("We're sorry but out of special concern for children's privacy, we do not knowingly accept online personal information from children under the age of 13. We do not knowingly allow children under the age of 13 to become registered members of our sites or buy products and services on our sites. We do not knowingly collect or solicit personal information about children under 13."))
            turbogears.redirect(redirect)
        test = select([PeopleTable.c.username], func.lower(PeopleTable.c.email)==email.lower()).execute().fetchall()
        if test:
            turbogears.flash(_("Sorry.  That email address is already in use. Perhaps you forgot your password?"))
            turbogears.redirect(redirect)
            return dict()
        person = People()
        person.username = username
        person.human_name = human_name
        person.telephone = telephone
        person.postal_address = postal_address
        person.email = email
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

http://fedoraproject.org/en/join-fedora

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

And finally, from all of us here at the Fedora Project, we're looking
forward to working with you!
''') % {'username': person.username,
        'password': newpass['pass'],
        'base_url': config.get('base_url_filter.base_url'),
        'webpath': config.get('server.webpath')})
        person.password = newpass['hash']
        return person
        
    @identity.require(identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.changepass")
    def changepass(self):
        return dict()

    @identity.require(identity.not_anonymous())
    @validate(validators=UserSetPassword())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.changepass")
    def setpass(self, currentpassword, password, passwordcheck): # pylint: disable-msg=W0613
        username = identity.current.user_name
        person  = People.by_username(username)

#        current_encrypted = generate_password(currentpassword)
#        print "PASS: %s %s" % (current_encrypted, person.password)
        if not person.password == crypt.crypt(currentpassword.encode('utf-8'), person.password):
            turbogears.flash('Your current password did not match')
            return dict()
        # TODO: Enable this when we need to.
        #if currentpassword == password:
        #    turbogears.flash('Your new password cannot be the same as your old one.')
        #    return dict()
        newpass = generate_password(password)
        try:
            person.old_password = person.password
            person.password = newpass['hash']
            person.password_changed = datetime.now(pytz.utc)
            Log(author_id=person.id, description='Password changed')
        # TODO: Make this catch something specific.
        except:
            Log(author_id=person.id, description='Password change failed!')
            turbogears.flash(_("Your password could not be changed."))
            return dict()
        else:   
            turbogears.flash(_("Your password has been changed."))
            turbogears.redirect('/user/view/%s' % identity.current.user_name)
            return dict()

    ### FIXME: error_handler does nothing without a validator
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.resetpass")
    def resetpass(self):
        if identity.not_anonymous():
            turbogears.flash(_('You are already logged in!'))
            turbogears.redirect('/user/view/%s' % identity.current.user_name)
        return dict()

    ### FIXME: error_handler does nothing without a validator
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.resetpass")
    def sendtoken(self, username, email, encrypted=False):
        # Logged in
        if identity.current.user_name:
            turbogears.flash(_("You are already logged in."))
            turbogears.redirect('/user/view/%s', identity.current.user_name)
            return dict()
        try:
            person = People.by_username(username)
        except InvalidRequestError:
            turbogears.flash(_('Username email combo does not exist!'))
            turbogears.redirect('/user/resetpass')

        if email != person.email:
            turbogears.flash(_("username + email combo unknown."))
            return dict()
        if person.status in ('expired', 'admin_disabled'):
            turbogears.flash(_("Your account currently has status %(status)s.  For more information, please contact %(admin_email)s") % \
                {'status': person.status, 'admin_email': config.get('accounts_email')})
            return dict()
        if person.status == ('bot'):
            turbogears.flash(_('System accounts cannot have their passwords reset online.  Please contact %(admin_email)s to have it reset') % \
                    {'admin_email': config.get('accounts_email')})
            reset_subject = 'Warning: attempted reset of system account'
            reset_text = '''
Warning: Someone attempted to reset the password for system account
%(account)s via the web interface.
''' % {'account': username}
            send_mail(config.get('accounts_email'), reset_subject, reset_text)
            return dict()

        token = generate_token()
        mail = _('''
Somebody (hopefully you) has requested a password reset for your account!
To change your password (or to cancel the request), please visit
https://admin.fedoraproject.org/accounts/user/verifypass/%(user)s/%(token)s
''') % {'user': username, 'token': token}
        if encrypted:
            # TODO: Move this out to mail function 
            # think of how to make sure this doesn't get
            # full of random keys (keep a clean Fedora keyring)
            # TODO: MIME stuff?
            keyid = re.sub('\s', '', person.gpg_keyid)
            if not keyid:
                turbogears.flash(_("This user does not have a GPG Key ID set, so an encrypted email cannot be sent."))
                return dict()
            ret = subprocess.call([config.get('gpgexec'), '--keyserver', config.get('gpg_keyserver'), '--recv-keys', keyid])
            if ret != 0:
                turbogears.flash(_("Your key could not be retrieved from subkeys.pgp.net"))
                turbogears.redirect('/user/resetpass')
                return dict()
            else:
                try:
                    # This may not be the neatest fix, but gpgme gave an error when mail was unicode.
                    plaintext = StringIO.StringIO(mail.encode('utf-8'))
                    ciphertext = StringIO.StringIO()
                    ctx = gpgme.Context()
                    ctx.armor = True
                    signer = ctx.get_key(re.sub('\s', '', config.get('gpg_fingerprint')))
                    ctx.signers = [signer]
                    recipient = ctx.get_key(keyid)
                    def passphrase_cb(uid_hint, passphrase_info, prev_was_bad, fd):
                        os.write(fd, '%s\n' % config.get('gpg_passphrase'))
                    ctx.passphrase_cb = passphrase_cb
                    ctx.encrypt_sign([recipient],
                        gpgme.ENCRYPT_ALWAYS_TRUST,
                        plaintext,
                        ciphertext)
                    mail = ciphertext.getvalue()
                except:
                    turbogears.flash(_('Your password reset email could not be encrypted.'))
                    return dict()
        send_mail(email, _('Fedora Project Password Reset'), mail)
        person.passwordtoken = token
        turbogears.flash(_('A password reset URL has been emailed to you.'))
        turbogears.redirect('/login')  
        return dict()

    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.verifypass")
    @validate(validators=VerifyPass())
    def verifypass(self, username, token, cancel=False):
        person = People.by_username(username)
        if person.status in ('expired', 'admin_disabled'):
            turbogears.flash(_("Your account currently has status %(status)s.  For more information, please contact %(admin_email)s") % \
                {'status': person.status, 'admin_email': config.get('accounts_email')})
            return dict()
        if not person.passwordtoken:
            turbogears.flash(_('You do not have any pending password changes.'))
            turbogears.redirect('/login')
            return dict()
        if person.passwordtoken != token:
            turbogears.flash(_('Invalid password change token.'))
            turbogears.redirect('/login')
            return dict()
        if cancel:
            person.passwordtoken = ''
            turbogears.flash(_('Your password reset has been canceled.  The password change token has been invalidated.'))
            turbogears.redirect('/login')
            return dict()
        person.filter_private()
        return dict(person=person, token=token)

    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.verifypass")
    @validate(validators=UserResetPassword())
    def setnewpass(self, username, token, password, passwordcheck):
        person = People.by_username(username)
        if person.status in ('expired', 'admin_disabled'):
            turbogears.flash(_("Your account currently has status %(status)s.  For more information, please contact %(admin_email)s") % \
                {'status': person.status, 'admin_email': config.get('accounts_email')})
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
            import crypt
            if person.old_password:
                if crypt.crypt(password.encode('utf-8'), person.old_password) == person.old_password:
                    turbogears.flash(_('Your password can not be the same as your old password.'))
                    return dict(person=person, token=token)
            person.status = 'active'
            person.status_change = datetime.now(pytz.utc)


        ''' Log this '''
        newpass = generate_password(password)
        person.old_password = person.password
        person.password = newpass['hash']
        person.password_changed = datetime.now(pytz.utc)
        person.passwordtoken = ''
        Log(author_id=person.id, description='Password changed')
        session.flush()

        turbogears.flash(_('You have successfully reset your password.  You should now be able to login below.'))
        turbogears.redirect('/login')
        return dict()

    @identity.require(identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="fas.templates.user.gencert")
    def gencert(self):
        return dict()

    ### FIXME: Without a validator, error_handler() does nothing
    @identity.require(identity.not_anonymous())
    @error_handler(error) # pylint: disable-msg=E0602
    @expose(template="genshi:fas.templates.user.gencertdisabled", allow_json=True, content_type='text/html')
    @expose(template="genshi-text:fas.templates.user.cert", format="text", content_type='application/x-x509-user-cert', allow_json=True)
    def dogencert(self):
        from cherrypy import response, request
        if not config.get('gencert', False):
            # Certificate generation is disabled on this machine
            # Return the error page
            return dict()
        import tempfile
        response.headers["content-disposition"] = "attachment"
        username = identity.current.user_name
        person = People.by_username(username)
        if CLADone(person):
            pkey = openssl_fas.createKeyPair(openssl_fas.TYPE_RSA, 2048)

            digest = config.get('openssl_digest')
            expire = config.get('openssl_expire')

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
            reqfile = tempfile.NamedTemporaryFile()
            reqfile.write(reqdump)
            reqfile.flush()

            certfile = tempfile.NamedTemporaryFile()
            while True:
                try:
                    os.mkdir(os.path.join(config.get('openssl_lockdir'), 'lock'))
                    break
                except OSError:
                    time.sleep(0.75)
            try:
                indexfile = open(config.get('openssl_ca_index'))
                for entry in indexfile:
                    attrs = entry.split('\t')
                    if attrs[0] != 'V':
                        continue
                    # the index line looks something like this:
                    # R\t090816180424Z\t080816190734Z\t01\tunknown\t/C=US/ST=Pennsylvania/O=Fedora/CN=test1/emailAddress=rickyz@cmu.edu
                    # V\t090818174940Z\t\t01\tunknown\t/C=US/ST=North Carolina/O=Fedora Project/OU=Upload Files/CN=toshio/emailAddress=badger@clingman.lan
                    dn = attrs[5]
                    serial = attrs[3]
                    info = {}
                    for pair in dn.split('/'):
                        if pair:
                            key, value = pair.split('=')
                            info[key] = value
                    if info['CN'] == person.username:
                        # revoke old certs
                        subprocess.call([config.get('makeexec'), '-C',
                            config.get('openssl_ca_dir'), 'revoke',
                            'cert=%s/%s' % (config.get('openssl_ca_newcerts'), serial + '.pem')])

                command = [config.get('makeexec'), '-C',
                        config.get('openssl_ca_dir'), 'sign',
                        'req=%s' % reqfile.name, 'cert=%s' % certfile.name]
                ret = subprocess.call(command)
            finally:
                os.rmdir(os.path.join(config.get('openssl_lockdir'), 'lock'))

            reqfile.close()
            if ret != 0:
                turbogears.flash(_('Your certificate could not be generated.'))
                turbogears.redirect('/home')
                return dict()
            certdump = certfile.read()
            certfile.close()
            keydump = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
            cherrypy.request.headers['Accept'] = 'text'

            gencert_subject = 'A new certificate has been generated for %s' % person.username
            gencert_text = '''
You have just generated a new SSL certificate.  If you did not request this,
please contact admin@fedoraproject.org and let them know.

Note that all certificates generated prior to the current one have been
automatically revoked, and should stop working within the hour.
'''
            send_mail(person.email, gencert_subject, gencert_text)
            return dict(tg_template="genshi-text:fas.templates.user.cert",
                    cla=True, cert=certdump, key=keydump)
        else:
            if self.jsonRequest():
                return dict(cla=False)
            turbogears.flash(_('Before generating a certificate, you must first complete the CLA.'))
            turbogears.redirect('/cla/')

