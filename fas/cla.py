# -*- coding: utf-8 -*-
''' Used for processing CLA requests'''
#
# Copyright © 2008  Ricky Zhou All rights reserved.
# Copyright © 2008-2009 Red Hat, Inc. All rights reserved.
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
#
import turbogears
from turbogears import controllers, expose, identity, config
from turbogears.database import session

import cherrypy

from sqlalchemy.exceptions import SQLError

from datetime import datetime
import GeoIP
from genshi.template.plugin import TextTemplateEnginePlugin

from fedora.tg.util import request_format

from fas.model import People, Groups, Log
from fas.auth import is_admin, cla_done
from fas.util import send_mail
import fas

from fas import _

class CLA(controllers.Controller):
    ''' Processes CLA workflow '''
    # Group name for people having signed the CLA
    CLAGROUPNAME = config.get('cla_fedora_group')
    # Meta group for everyone who has satisfied the requirements of the CLA
    # (By signing or having a corporate signatue or, etc)
    CLAMETAGROUPNAME = config.get('cla_done_group')

    # Values legal in phone numbers
    PHONEDIGITS = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '+',
            '-', ')' ,'(', ' ')

    def __init__(self):
        '''Create a CLA Controller.'''

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.cla.index")
    def index(self):
        '''Display the CLAs (and accept/do not accept buttons)'''
        show = {}
        show['show_postal_address'] = config.get('show_postal_address')

        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        try:
            code_len = len(person.country_code)
        except TypeError:
            code_len = 0
        if not person.telephone or code_len != 2 or \
            person.country_code == '  ':
            turbogears.flash('A valid country and telephone number are' +
                    ' required to complete the CLA.  Please fill them ' +
                    'out below.')
        cla = cla_done(person)
        person = person.filter_private()
        return dict(cla=cla, person=person, date=datetime.utcnow().ctime(),
                    show=show)

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

    def json_request(self):
        ''' Helps define if json is being used for this request

        :returns: 1 or 0 depending on if request is json or not
        '''

        return 'tg_format' in cherrypy.request.params and \
                cherrypy.request.params['tg_format'] == 'json'

    @expose(template="fas.templates.error")
    def error(self, tg_errors=None):
        '''Show a friendly error message'''
        if not tg_errors:
            turbogears.redirect('/')
        return dict(tg_errors=tg_errors)

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template = "genshi-text:fas.templates.cla.cla", format = "text",
            content_type = 'text/plain; charset=utf-8')
    def text(self):
        '''View CLA as text'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        person = person.filter_private()
        return dict(person=person, date=datetime.utcnow().ctime())

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template = "genshi-text:fas.templates.cla.cla", format = "text",
            content_type = 'text/plain; charset=utf-8')
    def download(self):
        '''Download CLA'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        person = person.filter_private()
        return dict(person=person, date=datetime.utcnow().ctime())

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.user.view", allow_json=True)
    def reject(self, person_name):
        '''Reject a user's CLA.

        This method will remove a user from the CLA group and any other groups
        that they are in that require the CLA.  It is used when a person has
        to fulfill some more legal requirements before having a valid CLA.

        Arguments
        :person_name: Name of the person to reject.
        '''
        show = {}
        show['show_postal_address'] = config.get('show_postal_address')
        exc = None
        user = People.by_username(turbogears.identity.current.user_name)
        if not is_admin(user):
            # Only admins can use this
            turbogears.flash(_('You are not allowed to reject CLAs.'))
            exc = 'NotAuthorized'
        else:
            # Unapprove the cla and all dependent groups
            person = People.by_username(person_name)
            for role in person.roles:
                if self._cla_dependent(role.group):
                    role.role_status = 'unapproved'
            try:
                session.flush()
            except SQLError, error:
                turbogears.flash(_('Error removing cla and dependent groups' \
                        ' for %(person)s\n Error was: %(error)s') %
                        {'person': person_name, 'error': str(error)})
                exc = 'sqlalchemy.SQLError'

        if not exc:
            # Send a message that the ICLA has been revoked
            date_time = datetime.utcnow()
            Log(author_id=user.id, description='Revoked %s CLA' %
                person.username, changetime=date_time)
            revoke_subject = 'Fedora ICLA Revoked'
            revoke_text = '''
Hello %(human_name)s,

We're sorry to bother you but we had to reject your CLA for now because
information you provided has been deemed incorrect.  The most common cause
of this is people abbreviating their name like "B L Couper" instead of
providing their actual full name "Bill Lay Couper".  Other causes of this
include are using a country, or phone number that isn't accurate [1]_.
If you could edit your account [2]_ to fix any of these problems and resubmit
the CLA we would appreciate it.

.. [1]: Why does it matter that we have your real name and phone
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
    ''' % {'username': person.username, 'human_name': person.human_name}

            send_mail(person.email, revoke_subject, revoke_text)

            # Yay, sweet success!
            turbogears.flash(_('CLA Successfully Removed.'))
        # and now we're done
        if request_format() == 'json':
            return_val = {}
            if exc:
                return_val['exc'] = exc
            return return_val
        else:
            turbogears.redirect('/user/view/%s' % person_name)

    @identity.require(turbogears.identity.not_anonymous())
    @expose(template="fas.templates.cla.index")
    def send(self, human_name, telephone, country_code, postal_address=None,
        confirm=False, agree=False):
        '''Send CLA'''
        username = turbogears.identity.current.user_name
        person = People.by_username(username)
        if cla_done(person):
            turbogears.flash(_('You have already completed the CLA.'))
            turbogears.redirect('/cla/')
            return dict()
        if not agree:
            turbogears.flash(_("You have not completed the CLA."))
            turbogears.redirect('/user/view/%s' % person.username)
        if not confirm:
            turbogears.flash(_(
                'You must confirm that your personal information is accurate.'
            ))
            turbogears.redirect('/cla/')

        # Compare old information to new to see if any changes have been made
        if human_name and person.human_name != human_name:
            person.human_name = human_name
        if telephone and person.telephone != telephone:
            person.telephone = telephone
        if postal_address and person.postal_address != postal_address:
            person.postal_address = postal_address
        if country_code and person.country_code != country_code:
            person.country_code = country_code
        # Save it to the database
        try:
            session.flush()
        except Exception:
            turbogears.flash(_("Your updated information could not be saved."))
            turbogears.redirect('/cla/')
            return dict()

        # Heuristics to detect bad data
        if not person.telephone or \
                not person.human_name or \
                not person.country_code:
            turbogears.flash(_('To complete the CLA, we must have your ' + \
                'name telephone number, and country.  Please ensure they ' + \
                'have been filled out.'))
            turbogears.redirect('/cla/')

        blacklist = config.get('country_blacklist', [])
        country_codes = [c for c in GeoIP.country_codes if c not in blacklist]

        if person.country_code not in country_codes:
            turbogears.flash(_('To complete the CLA, a valid country code' + \
            'must be specified.  Please select one now.'))
            turbogears.redirect('/cla/')
        if [True for char in person.telephone if char not in self.PHONEDIGITS]:
            turbogears.flash(_('Telephone numbers can only consist of ' + \
                'numbers, "-", "+", "(", ")", or " ".  Please reenter using' +\
                'only those characters.'))
            turbogears.redirect('/cla/')
            turbogears.redirect('/cla/')

        group = Groups.by_name(self.CLAGROUPNAME)
        try:
            # Everything is correct.
            person.apply(group, person) # Apply for the new group
            session.flush()
        except fas.ApplyError:
            # This just means the user already is a member (probably
            # unapproved) of this group
            pass
        except Exception:
            turbogears.flash(_("You could not be added to the '%s' group.") %
                                group.name)
            turbogears.redirect('/cla/')
            return dict()

        try:
            # Everything is correct.
            person.sponsor(group, person) # Sponsor!
            session.flush()
        except fas.SponsorError:
            turbogears.flash(_("You are already a part of the '%s' group.") %
                                group.name)
            turbogears.redirect('/cla/')
        except:
            turbogears.flash(_("You could not be added to the '%s' group.") %
                                group.name)
            turbogears.redirect('/cla/')

        date_time = datetime.utcnow()
        Log(author_id = person.id, description = 'Completed CLA',
            changetime = date_time)
        cla_subject = \
            'Fedora ICLA completed for %(human_name)s (%(username)s)' % \
            {'username': person.username, 'human_name': person.human_name}
        cla_text = '''
Fedora user %(username)s has completed an ICLA (below).
Username: %(username)s
Email: %(email)s
Date: %(date)s

If you need to revoke it, please visit this link:
    https://admin.fedoraproject.org/accounts/cla/reject/%(username)s

=== CLA ===

''' % {'username': person.username,
'email': person.email,
'date': date_time.ctime(),}
        # Sigh..  if only there were a nicer way.
        plugin = TextTemplateEnginePlugin()
        cla_text += plugin.transform(dict(person=person),
                    'fas.templates.cla.cla').render(method='text',
                    encoding=None)

        send_mail(config.get('legal_cla_email'), cla_subject, cla_text)

        turbogears.flash(_("You have successfully completed the CLA.  You " + \
                            "are now in the '%s' group.") % group.name)
        turbogears.redirect('/user/view/%s' % person.username)
        return dict()
