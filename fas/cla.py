import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler

import ldap
import cherrypy

from datetime import datetime
import re
import gpgme
import StringIO

import fas.fasLDAP

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

from fas.auth import *

from fas.user import knownUser, userNameExists

class CLA(controllers.Controller):

    def __init__(self):
        '''Create a CLA Controller.'''

    @expose(template="fas.templates.cla.index")
    def index(self):
        '''Display an explanatory message about the Click-through and Signed CLAs (with links)'''
        username = turbogears.identity.current.user_name
        signedCLA = signedCLAPrivs(username)
        clickedCLA = clickedCLAPrivs(username)
        return dict(signedCLA=signedCLA, clickedCLA=clickedCLA)

    def jsonRequest(self):
        return 'tg_format' in cherrypy.request.params and \
                cherrypy.request.params['tg_format'] == 'json'

    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(turbogears.identity.not_anonymous())
    @error_handler(error)
    @expose(template="fas.templates.cla.view")
    def view(self, type=None):
        '''View CLA'''
        username = turbogears.identity.current.user_name
        if type == 'click':
            if signedCLAPrivs(username):
                turbogears.flash(_('You have already signed the CLA, so it is unnecessary to complete the Click-through CLA.'))
                turbogears.redirect('/cla')
                return dict()
            if clickedCLAPrivs(username):
                turbogears.flash(_('You have already completed the Click-through CLA.'))
                turbogears.redirect('/cla')
                return dict()
        elif type == 'sign':
            if signedCLAPrivs(username):
                turbogears.flash(_('You have already signed the CLA.'))
                turbogears.redirect('/cla')
                return dict()
        elif type != None:
            turbogears.redirect('/cla')
            return dict()
        username = turbogears.identity.current.user_name
        user = Person.by_username(username)
        return dict(type=type, user=user, date=datetime.utcnow().ctime())

    @identity.require(turbogears.identity.not_anonymous())
    @error_handler(error)
    @expose(template="genshi-text:fas.templates.cla.cla", format="text", content_type='text/plain; charset=utf-8')
    def download(self, type=None):
        '''Download CLA'''
        username = turbogears.identity.current.user_name
        user = Person.by_username(username)
        return dict(user=user, date=datetime.utcnow().ctime())

    @identity.require(turbogears.identity.not_anonymous())
    @error_handler(error)
    @expose(template="fas.templates.cla.index")
    def sign(self, signature):
        '''Sign CLA'''
        username = turbogears.identity.current.user_name
        if signedCLAPrivs(username):
            turbogears.flash(_('You have already signed the CLA.'))
            turbogears.redirect('/cla')
            return dict()
        groupname = config.get('cla_sign_group')
        group = Groups.by_name(groupname)
        ctx = gpgme.Context()
        data = StringIO.StringIO(signature.file.read())
        plaintext = StringIO.StringIO()
        verified = False
        person = Person.by_username(username)
        try:
            sigs = ctx.verify(data, None, plaintext)
        except gpgme.GpgmeError, e:
            turbogears.flash(_("Your signature could not be verified: '%s'.") % e)
            turbogears.redirect('/cla/view/sign')
            return dict()
        else:
            if len(sigs):
                sig = sigs[0]
                # This might still assume a full fingerprint. 
                fingerprint = sig.fpr
                if fingerprint != re.sub('\s', '', person.gpg_keyid):
                    turbogears.flash(_("Your signature's fingerprint did not match the fingerprint registered in FAS."))
                    turbogears.redirect('/cla/view/sign')
                    return dict()
                key = ctx.get_key(fingerprint)
                emails = [];
                for uid in key.uids:
                    emails.extend([uid.email])
                if person.emails['cla'].email in emails:
                    verified = True
                else:
                    turbogears.flash(_('Your key did not match your email.'))
                    turbogears.redirect('/cla/view/sign')
                    return dict()

        # We got a properly signed CLA.
        cla = plaintext.getvalue()
        if cla.find('Contributor License Agreement (CLA)') < 0:
            turbogears.flash(_('The GPG-signed part of the message did not contain a signed CLA.'))
            turbogears.redirect('/cla/view/sign')
            return dict()
        if re.compile('If you agree to these terms and conditions, type "I agree" here: I agree', re.IGNORECASE).match(cla):
            turbogears.flash(_('The text "I agree" was not found in the CLA.'))
            turbogears.redirect('/cla/view/sign')
            return dict()

        # Everything is correct.
        try:
            person.apply(group, person) # Apply...
            group.sponsor_person(person, person) # Approve...
        except:
            turbogears.flash(_("You could not be added to the '%s' group.") % groupname)
            turbogears.redirect('/cla/view/sign')
            return dict()
        else:
            try:
                clickgroup = Groups.by_name(config.get('cla_click_group'))
                clickgroup.remove_person(person, person)
            except:
                pass
            turbogears.flash(_("You have successfully signed the CLA.  You are now in the '%s' group.") % groupname)
            turbogears.redirect('/cla')
            return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @error_handler(error)
    @expose(template="fas.templates.cla.index")
    def click(self, agree):
        '''Click-through CLA'''
        username = turbogears.identity.current.user_name
        if signedCLAPrivs(username):
            turbogears.flash(_('You have already signed the CLA, so it is unnecessary to complete the Click-through CLA.'))
            turbogears.redirect('/cla')
            return dict()
        if clickedCLAPrivs(username):
            turbogears.flash(_('You have already completed the Click-through CLA.'))
            turbogears.redirect('/cla')
            return dict()
        groupname = config.get('cla_click_group')
        if agree.lower() == 'i agree':
            try:
                person = People.by_username(username)
                group = Groups.by_name(groupname)
                person.apply(group, person) # Apply...
                group.sponsor_person(person, person) # Approve...
            except:
                turbogears.flash(_("You could not be added to the '%s' group.") % groupname)
                turbogears.redirect('/cla/view/click')
                return dict()
            else:
                turbogears.flash(_("You have successfully agreed to the click-through CLA.  You are now in the '%s' group.") % groupname)
                turbogears.redirect('/cla')
                return dict()
        else:
            turbogears.flash(_("You have not agreed to the click-through CLA.") % groupname)
            turbogears.redirect('/cla/view/click')
            return dict()

