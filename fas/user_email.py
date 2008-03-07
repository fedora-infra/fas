import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler, config
from turbogears.database import session
import cherrypy

from fas.model import People
from fas.model import PersonEmails
from fas.model import EmailPurposes
from fas.model import Log

class NonFedoraEmail(validators.FancyValidator): 
    '''Make sure that an email address is not @fedoraproject.org''' 
    def _to_python(self, value, state): 
        return value.strip() 
    def validate_python(self, value, state): 
        if value.endswith('@fedoraproject.org'): 
            raise validators.Invalid(_("To prevent email loops, your email address cannot be @fedoraproject.org."), value, state) 

class EmailCreate(validators.Schema):
    email = validators.All(
        validators.Email(not_empty=True, strip=True),
        NonFedoraEmail(not_empty=True, strip=True),
    )
    #fedoraPersonBugzillaMail = validators.Email(strip=True)
    postal_address = validators.String(max=512)

class Email(controllers.Controller):

    def __init__(self):
        '''Create an Email Controller.
        '''

    @identity.require(turbogears.identity.not_anonymous())
    def index(self):
        '''Redirect to manage
        '''
        turbogears.redirect('/user/email/manage/%s' % turbogears.identity.current.user_name)


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
    def manage(self, username=None):
        '''
        Manage a person's emails.
        '''
        if not username:
            username = turbogears.identity.current.user_name
        person = People.by_username(username)
        return dict(person=person)

