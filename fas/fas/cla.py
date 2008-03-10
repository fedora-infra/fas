import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import cherrypy

from datetime import datetime
import re
import gpgme
import StringIO
import subprocess
import turbomail

from fas.auth import *

class CLA(controllers.Controller):

    def __init__(self):
        '''Create a CLA Controller.'''

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.cla.index")
    def index(self):
        '''Display an explanatory message about the Click-through and Signed CLAs (with links)'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        signedCLA = signedCLAPrivs(person)
        clickedCLA = clickedCLAPrivs(person)
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
        person = People.by_username(username)
        if not person.telephone or \
            not person.postal_address or \
            not person.gpg_keyid:
                turbogears.flash(_('To sign the CLA we must have your telephone number, postal address and gpg key id.  Please ensure they have been filled out'))
                turbogears.redirect('/user/edit/%s' % username)

        if type == 'click':
            # Disable click-through CLA for now
            #if signedCLAPrivs(person):
            #    turbogears.flash(_('You have already signed the CLA, so it is unnecessary to complete the Click-through CLA.'))
            #    turbogears.redirect('/cla/')
            #    return dict()
            #if clickedCLAPrivs(person):
            #    turbogears.flash(_('You have already completed the Click-through CLA.'))
            #    turbogears.redirect('/cla/')
            #    return dict()
            turbogears.redirect('/cla/')
            return dict()
        elif type == 'sign':
            if signedCLAPrivs(person):
                turbogears.flash(_('You have already signed the CLA.'))
                turbogears.redirect('/cla/')
                return dict()
        elif type != None:
            turbogears.redirect('/cla/')
            return dict()
        return dict(type=type, person=person, date=datetime.utcnow().ctime())

    @identity.require(turbogears.identity.not_anonymous())
    @error_handler(error)
    @expose(template="genshi-text:fas.templates.cla.cla", format="text", content_type='text/plain; charset=utf-8')
    def download(self, type=None):
        '''Download CLA'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        return dict(person=person, date=datetime.utcnow().ctime())

    @identity.require(turbogears.identity.not_anonymous())
    @error_handler(error)
    @expose(template="fas.templates.cla.index")
    def sign(self, signature):
        '''Sign CLA'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        
        if signedCLAPrivs(person):
            turbogears.flash(_('You have already signed the CLA.'))
            turbogears.redirect('/cla/')
            return dict()
        groupname = config.get('cla_sign_group')
        group = Groups.by_name(groupname)

        ctx = gpgme.Context()
        data = StringIO.StringIO(signature.file.read())
        plaintext = StringIO.StringIO()
        verified = False
        keyid = re.sub('\s', '', person.gpg_keyid)
        ret = subprocess.call([config.get('gpgexec'), '--keyserver', config.get('gpg_keyserver'), '--recv-keys', keyid])
        if ret != 0:
            turbogears.flash(_("Your key could not be retrieved from subkeys.pgp.net"))
            turbogears.redirect('/cla/view/sign')
            return dict()
        #try:
        #      subprocess.check_call([config.get('gpgexec'), '--keyserver', config.get('gpg_keyserver'), '--recv-keys', keyid])
        #except subprocess.CalledProcessError:
        #    turbogears.flash(_("Your key could not be retrieved from subkeys.pgp.net"))
        #    turbogears.redirect('/cla/view/sign')
        #    return dict()
        else:
            try:
                sigs = ctx.verify(data, None, plaintext)
            except gpgme.GpgmeError, e:
                turbogears.flash(_("Your signature could not be verified: '%s'.") % e)
                turbogears.redirect('/cla/view/sign')
                return dict()
            else: # Hm, I wonder how these nested ifs can be made more elegant...
                if len(sigs):
                    sig = sigs[0]
                    # This might still assume a full fingerprint. 
                    key = ctx.get_key(keyid)
                    fpr = key.subkeys[0].fpr
                    if sig.fpr != fpr:
                        turbogears.flash(_("Your signature's fingerprint did not match the fingerprint registered in FAS."))
                        turbogears.redirect('/cla/view/sign')
                        return dict()
                    emails = [];
                    for uid in key.uids:
                        emails.extend([uid.email])
                    if person.emails['primary'] in emails:
                        verified = True
                    else:
                        turbogears.flash(_('Your key did not match your email.'))
                        turbogears.redirect('/cla/view/sign')
                        return dict()
                else:
                    # TODO: Find out what it means if verify() succeeded and len(sigs) == 0
                    turbogears.flash(_('len(sigs) == 0'))
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
                session.flush()
                person.sponsor(group, person) # Approve...
                session.flush()
            except:
                # TODO: If apply succeeds and sponsor fails, the user has
                # to remove themselves from the CLA group before they can
                # sign the CLA and go through the above try block again.
                turbogears.flash(_("You could not be added to the '%s' group.") % group.name)
                turbogears.redirect('/cla/view/sign')
                return dict()
            else:
                try:
                    clickgroup = Groups.by_name(config.get('cla_click_group'))
                    person.remove(cilckgroup, person)
                except:
                    pass
                message = turbomail.Message(config.get('accounts_email'), config.get('legal_cla_email'), 'Fedora ICLA completed')
                message.plain = '''
Fedora user %(username)s has signed a completed ICLA using their published GPG key, ID %(gpg_keyid)s,
that is associated with e-mail address %(email)s. The full signed ICLA is attached.
''' % {'username': person.username, 'gpg_keyid': person.gpg_keyid, 'email': person.emails['primary']}
                signature.file.seek(0) # For another read()
                message.attach(signature.file, signature.filename)
                turbomail.enqueue(message)
                turbogears.flash(_("You have successfully signed the CLA.  You are now in the '%s' group.") % group.name)
                turbogears.redirect('/cla/')
                return dict()

    @identity.require(turbogears.identity.not_anonymous())
    @error_handler(error)
    # Don't expose click-through CLA for now.
    #@expose(template="fas.templates.cla.index")
    def click(self, agree):
        '''Click-through CLA'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)

        if signedCLAPrivs(person):
            turbogears.flash(_('You have already signed the CLA, so it is unnecessary to complete the Click-through CLA.'))
            turbogears.redirect('/cla/')
            return dict()
        if clickedCLAPrivs(person):
            turbogears.flash(_('You have already completed the Click-through CLA.'))
            turbogears.redirect('/cla/')
            return dict()
        groupname = config.get('cla_click_group')
        group = Groups.by_name(groupname)
        if agree.lower() == 'i agree':
            try:
                person.apply(group, person) # Apply...
                session.flush()
                person.sponsor(group, person) # Approve...
                session.flush()
            except:
                turbogears.flash(_("You could not be added to the '%s' group.") % group.name)
                turbogears.redirect('/cla/view/click')
                return dict()
            else:
                turbogears.flash(_("You have successfully agreed to the click-through CLA.  You are now in the '%s' group.") % group.name)
                turbogears.redirect('/cla/')
                return dict()
        else:
            turbogears.flash(_("You have not agreed to the click-through CLA.") % group.name)
            turbogears.redirect('/cla/view/click')
            return dict()

