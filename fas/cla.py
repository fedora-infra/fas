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
#
import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

import cherrypy

from datetime import datetime
import re
import turbomail
from genshi.template.plugin import TextTemplateEnginePlugin

from fas.model import People
from fas.model import Log
from fas.auth import *

class CLA(controllers.Controller):

    def __init__(self):
        '''Create a CLA Controller.'''

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.cla.index")
    def index(self):
        '''Display the CLAs (and accept/do not accept buttons)'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if not person.telephone or not person.postal_address:
            turbogears.flash('A valid postal Address and telephone number are required to complete the CLA.  Please fill them out below.')
            turbogears.redirect('/user/edit/%s' % username)
        cla = CLADone(person)
        return dict(cla=cla, person=person, date=datetime.utcnow().ctime())

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
    @expose(template="genshi-text:fas.templates.cla.cla", format="text", content_type='text/plain; charset=utf-8')
    def text(self, type=None):
        '''View CLA as text'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        return dict(person=person, date=datetime.utcnow().ctime())

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
    def send(self, confirm=False, agree=False):
        '''Send CLA'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if CLADone(person):
            turbogears.flash(_('You have already completed the CLA.'))
            turbogears.redirect('/cla/')
            return dict()
        if not agree:
            turbogears.flash(_("You have not completed the CLA."))
            turbogears.redirect('/user/view/%s' % person.username)
        if not person.telephone or \
            not person.postal_address:
            turbogears.flash(_('To complete the CLA, we must have your telephone number and postal address.  Please ensure they have been filled out.'))
            turbogears.redirect('/user/edit/%s' % username)
        if not confirm:
            turbogears.flash(_('You must confirm that your personal information is accurate.'))
            turbogears.redirect('/cla/')
        groupname = config.get('cla_fedora_group')
        group = Groups.by_name(groupname)
        try:
            # Everything is correct.
            person.apply(group, person) # Apply...
            session.flush()
            person.sponsor(group, person) # Sponsor!
        except:
            # TODO: If apply succeeds and sponsor fails, the user has
            # to remove themselves from the CLA group before they can
            # complete the CLA and go through the above try block again.
            turbogears.flash(_("You could not be added to the '%s' group.") % group.name)
            turbogears.redirect('/cla/')
            return dict()
        else:
            dt = datetime.utcnow()
            Log(author_id=person.id, description='Completed CLA', changetime=dt)
            message = turbomail.Message(config.get('accounts_email'), config.get('legal_cla_email'), 'Fedora ICLA completed')
            message.plain = '''
Fedora user %(username)s has completed an ICLA (below).
Username: %(username)s
Email: %(email)s
Date: %(date)s

=== CLA ===

''' % {'username': person.username,
    'human_name': person.human_name,
    'email': person.email,
    'postal_address': person.postal_address,
    'telephone': person.telephone,
    'facsimile': person.facsimile,
    'date': dt.ctime(),}
            # Sigh..  if only there were a nicer way.
            plugin = TextTemplateEnginePlugin()
            message.plain += plugin.render(template='fas.templates.cla.cla', info=dict(person=person), format='text')
            turbomail.enqueue(message)
            turbogears.flash(_("You have successfully completed the CLA.  You are now in the '%s' group.") % group.name)
            turbogears.redirect('/user/view/%s' % person.username)
            return dict()

