import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler, config
from turbogears.database import session
import cherrypy

import turbomail
import random

from fas.model import People
from fas.model import PersonEmails
from fas.model import EmailPurposes
from fas.model import Log

from fas.auth import *

class NonFedoraEmail(validators.FancyValidator): 
    '''Make sure that an email address is not @fedoraproject.org''' 
    def _to_python(self, value, state): 
        return value.strip() 
    def validate_python(self, value, state): 
        if value.endswith('@fedoraproject.org'): 
            raise validators.Invalid(_("To prevent email loops, your email address cannot be @fedoraproject.org."), value, state) 

class EmailSave(validators.Schema):
    email = validators.All(
        validators.Email(not_empty=True, strip=True),
        NonFedoraEmail(not_empty=True, strip=True),
    )
    description = validators.String(not_empty=True, max=512)

def generate_validtoken(length=32):
    ''' Generate Validation Token '''
    chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    token = ''
    for i in xrange(length):
        token += random.choice(chars)
    return token

class Email(controllers.Controller):

    def __init__(self):
        '''Create an Email Controller.
        '''

    @identity.require(turbogears.identity.not_anonymous())
    def index(self):
        '''Redirect to manage
        '''
        turbogears.redirect('/user/email/manage')


    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(turbogears.identity.not_anonymous())
    #@validate(validators=UserView())
    @error_handler(error)
    @expose(template="fas.templates.user.email.manage", allow_json=True)
    def manage(self, targetname=None):
        '''
        Manage a person's emails
        '''
        # TODO: Some sort of auth checking - other people should
        # probably be limited to looking at a person's email through
        # /user/view, although admins should probably be able to set
        # emails (with/without verification?)
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        if targetname:
            target = People.by_username(targetname)
        else:
            target = person

        return dict(target=target)

    @identity.require(turbogears.identity.not_anonymous())
    #@validate(validators=UserView())
    @error_handler(error)
    @expose(template="fas.templates.user.email.add", allow_json=True)
    def add(self, targetname=None):
        '''
        Display the form to add an email
        '''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        if targetname:
            target = People.by_username(targetname)
        else:
            target = person

        if not canEditUser(person, target):
            turbogears.flash(_('You cannot edit %s') % target.username )
            turbogears.redirect('/user/email/manage')
            return dict()

        return dict(target=target)

    @identity.require(turbogears.identity.not_anonymous())
    @validate(validators=EmailSave())
    @error_handler(error)
    @expose(template="fas.templates.user.email.add", allow_json=True)
    def save(self, targetname, email, description):
        '''
        Display the form to add an email
        '''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        if targetname:
            target = People.by_username(targetname)
        else:
            target = person

        if not canEditUser(person, target):
            turbogears.flash(_('You cannot edit %s') % target.username )
            turbogears.redirect('/user/email/manage')
            return dict()

        validtoken = generate_validtoken()

        try:
            person_email = PersonEmails()
            person_email.email = email
            person_email.person = target
            person_email.description = description
            person_email.validtoken = validtoken
            session.flush()
        # Hmm, should this be checked in the validator or here?
        except IntegrityError:
            turbogears.flash(_('The email \'%s\' is already in used.') % email)
            return dict(target=target)
        else:
            # TODO: Make this email more friendly.  Maybe escape the @ in email too?
            validurl = config.get('base_url_filter.base_url') + turbogears.url('/user/email/verify/%s/%s/%s') % (target.username, email, validtoken)
            message = turbomail.Message(config.get('accounts_mail'), email, _('Confirm this email address'))
            message.plain = _('''
Go to this URL to verify that you own this email address: %s
''') % validurl
            turbomail.enqueue(message)
            turbogears.flash(_('Your email has been added.  Before you can use this email, you must verify it.  The email you added should receive a message with instructions shortly.'))

            return dict(target=target)

        return dict(target=target)

    @identity.require(turbogears.identity.not_anonymous())
    # TODO: Validation!
    #@validate(validators=UserView())
    @error_handler(error)
    @expose(allow_json=True)
    def verify(self, targetname, email, validtoken):
        '''
        Verify an email
        '''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        if targetname:
            target = People.by_username(targetname)
        else:
            target = person

        if not canEditUser(person, target):
            turbogears.flash(_('You cannot edit %s') % target.username )
            turbogears.redirect('/user/email/manage')
            return dict()

        if target.person_emails[email].verified:
            turbogears.flash(_('The email provided has already been verified.'))
            turbogears.redirect('/user/email/manage')
            return dict()

        try:
            if target.person_emails[email].validtoken == validtoken:
                target.person_emails[email].validtoken = ''
                target.person_emails[email].verified = True
                turbogears.flash(_('Your email has been successfully verified.'))
                turbogears.redirect('/user/email/manage')
                return dict()
            else:
                turbogears.flash(_('The verification string did not match.'))
                turbogears.redirect('/user/email/manage')
                return dict()
        except KeyError:
            turbogears.flash(_('No such email is associated with your user.'))
            turbogears.redirect('/user/email/manage')
            return dict()

