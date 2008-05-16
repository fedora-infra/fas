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

from sqlalchemy.exceptions import SQLError

from datetime import datetime
import re
import turbomail
from genshi.template.plugin import TextTemplateEnginePlugin

from fedora.tg.util import request_format

from fas.model import People
from fas.model import Log
from fas.auth import *
# import * isn't good practice.  Remove when we have all the improts in the
# line below:
from fas.auth import isAdmin
import fas

class CLA(controllers.Controller):

    # Group name for people having signed the CLA
    CLAGROUPNAME = config.get('cla_fedora_group')
    # Meta group for everyone who has satisfied the requirements of the CLA
    # (By signing or having a corporate signatue or, etc)
    CLAMETAGROUPNAME = config.get('cla_done_group')

    def __init__(self):
        '''Create a CLA Controller.'''

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.cla.index")
    def index(self):
        '''Display the CLAs (and accept/do not accept buttons)'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        try:
            code_len = len(person.country_code)
        except TypeError:
            code_len = 0
        print "%s - %s" % (person.country_code, code_len)
        if not person.telephone or not person.postal_address or code_len != 2 or person.country_code=='  ':
            turbogears.flash('A valid postal Address, country and telephone number are required to complete the CLA.  Please fill them out below.')
            turbogears.redirect('/user/edit/%s' % username)
        cla = CLADone(person)
        return dict(cla=cla, person=person, date=datetime.utcnow().ctime())

    def _cla_dependent(self, group):
        '''
        Check whether a group has the cla in its prerequisite chain.

        Arguments:
        :group: group to check

        Returns: True if the group requires the cla_group_name otherwise
        '''
        if group.name in (self.CLAGROUPNAME, self.CLAMETAGROUPNAME):
            return True
        if group.prerequisite_id:
            return self._cla_dependent(group.prerequisite)
        return False

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
    @expose(template="fas.templates.user.view", allow_json=True)
    def reject(self, personName):
        '''Reject a user's CLA.

        This method will remove a user from the CLA group and any other groups
        that they are in that require the CLA.  It is used when a person has
        to fulfill some more legal requirements before having a valid CLA.

        Arguments
        :personName: Name of the person to reject.
        '''
        exc = None
        user = People.by_username(turbogears.identity.current.user_name)
        if not isAdmin(user):
            # Only admins can use this
            turbogears.flash(_('You are not allowed to reject CLAs.'))
            exc = 'NotAuthorized'
        else:
            # Unapprove the cla and all dependent groups
            person = People.by_username(personName)
            for role in person.approved_roles:
                if self._cla_dependent(role.group):
                    role.role_status = 'unapproved'
            try:
                session.flush()
            except SQLError, e:
                turbogears.flash(_('Error removing cla and dependent groups' \
                        ' for %(person)s\n Error was: %(error)s') %
                        {'person': personName, 'error': str(e)})
                exc = 'sqlalchemy.SQLError'

        if not exc:
            # Send a message that the ICLA has been revoked
            dt = datetime.utcnow()
            Log(author_id=user.id, description='Revoked %s CLA' % person.username, changetime=dt)
            message = turbomail.Message(config.get('accounts_email'), person.email, 'Fedora ICLA Revoked')
            message.plain = '''
Hello %(human_name)s,

We're sorry to bother you but we had to reject your CLA for now because
information you provided has been deemed incorrect.  Common causes of this
are using a name, address/country, or phone number that isn't accurate [1]_.  
If you could edit your account [2]_ to fix any of these problems and resubmit
the CLA we would appreciate it.

.. [1]: Why does it matter that we have your real name, address and phone
        number?   It's because the CLA is a legal document and should we ever
        need to contact you about one of your contributions (as an example,
        because someone contacts *us* claiming that it was really they who
        own the copyright to the contribution) we might need to contact you
        for more information about what's going on.

.. [2]: Edit your account by logging in at this URL:
        https://admin.fedoraproject.org/accounts/user/edit/%(username)s

If you have questions about what specifically might be the problem with your
account, please contact us at accounts@fedoraproject.org.

Thanks!
    ''' % {'username': person.username,
    'human_name': person.human_name, }
            turbomail.enqueue(message)

            # Yay, sweet success!
            turbogears.flash(_('CLA Successfully Removed.'))

        # and now we're done
        if request_format() == 'json':
            returnVal = {}
            if exc:
                returnVal['exc'] = exc
            return returnVal
        else:
            turbogears.redirect('/user/view/%s' % personName)

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
        group = Groups.by_name(self.CLAGROUPNAME)
        try:
            # Everything is correct.
            person.apply(group, person) # Apply for the new group
            session.flush()
        except fas.ApplyError, e:
            # This just means the user already is a member (probably
            # unapproved) of this group
            pass
        except Exception, e:
            print e
            # TODO: If apply succeeds and sponsor fails, the user has
            # to remove themselves from the CLA group before they can
            # complete the CLA and go through the above try block again.
            turbogears.flash(_("You could not be added to the '%s' group. 1111") % group.name)
            turbogears.redirect('/cla/')
            return dict()

        try:
            # Everything is correct.
            person.sponsor(group, person) # Sponsor!
            session.flush()
        except fas.SponsorError:
            turbogears.flash(_("You are already a part of the '%s' group.") % group.name)
            turbogears.redirect('/cla/')
        except:
            # TODO: If apply succeeds and sponsor fails, the user has
            # to remove themselves from the CLA group before they can
            # complete the CLA and go through the above try block again.
            turbogears.flash(_("You could not be added to the '%s' group. 222") % group.name)
            turbogears.redirect('/cla/')

        dt = datetime.utcnow()
        Log(author_id=person.id, description='Completed CLA', changetime=dt)
        message = turbomail.Message(config.get('accounts_email'), config.get('legal_cla_email'), 'Fedora ICLA completed')
        message.plain = '''
Fedora user %(username)s has completed an ICLA (below).
Username: %(username)s
Email: %(email)s
Date: %(date)s

If you need to revoke it, please visit this link:
    https://admin.fedoraproject.org/accounts/cla/reject/%(username)s

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
