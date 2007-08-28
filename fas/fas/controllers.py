from turbogears import controllers, expose, config
# from model import *
from turbogears import identity, redirect, widgets, validate, validators, error_handler
from cherrypy import request, response
from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup
from turbogears import exception_handler
import turbogears
import ldap
import time
from operator import itemgetter

from fas.user import User
from fas.group import Group

from fas.auth import isAdmin, canAdminGroup, canSponsorGroup, canEditUser

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# from fas import json
# import logging
# log = logging.getLogger("fas.controllers")

#TODO: Appropriate flash icons for errors, etc.

class Root(controllers.RootController):

    user = User()
    group = Group()

    @expose(template="fas.templates.welcome")
    # @identity.require(identity.in_group("admin"))
    def index(self):
        if turbogears.identity.not_anonymous():
            turbogears.redirect('home')
        return dict(now=time.ctime())

    @expose(template="fas.templates.home")
    @identity.require(identity.not_anonymous())
    def home(self):
        from feeds import Koji
        builds = Koji(turbogears.identity.current.user_name)
        return dict(builds=builds)

    @expose(template="fas.templates.login")
    def login(self, forward_url=None, previous_url=None, *args, **kw):

        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            turbogears.flash(_('Welcome, %s') % Person.byUserName(turbogears.identity.current.user_name).givenName)
            raise redirect(forward_url)

        forward_url=None
        previous_url= request.path

        if identity.was_login_attempted():
            msg=_("The credentials you supplied were not correct or "
                   "did not grant access to this resource.")
        elif identity.get_identity_errors():
            msg=_("You must provide your credentials before accessing "
                   "this resource.")
        else:
            msg=_("Please log in.")
            forward_url= request.headers.get("Referer", "/")

        response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=request.params,
                    forward_url=forward_url)

    @expose()
    def logout(self):
        identity.current.logout()
        turbogears.flash(_('You have successfully logged out.'))
        raise redirect("/")

    ## TODO: Invitation cleanup- move out and validate!
    @expose(template='fas.templates.inviteMember')
    @identity.require(identity.not_anonymous())
    def inviteMember(self, name=None, email=None, skills=None):
        if name and email:
            turbogears.flash(_('Invitation Sent to: "%(name)s" <%(email)s>') % {'name': name, 'email': email})
        if name or email:#FIXME
            turbogears.flash(_('Please provide both an email address and the persons name.'))
        return dict()

    @expose(format="json")
    def search(self, userName=None, groupName=None):
        people = Person.users('%s*' % userName)
        return dict(people=
                filter(lambda item: userName in item.lower(), people))

    @expose(template='fas.templates.invite')
    @identity.require(identity.not_anonymous())
    def invite(self, target=None):
        import turbomail
        user = Person.byUserName(turbogears.identity.current.user_name)
        if target:
            message = turbomail.Message(user.mail, target, _('Come join The Fedora Project!'))
#            message.plain = "Please come join the fedora project!  Someone thinks your skills and abilities may be able to help our project.  If your interested please go to http://fedoraproject.org/wiki/HelpWanted"
            message.plain = _("%(name)s <%(email)s> has invited you to join the Fedora \
Project!  We are a community of users and developers who produce a \
complete operating system from entirely free and open source software \
(FOSS).  %(name)s thinks that you have knowledge and skills \
that make you a great fit for the Fedora community, and that you might \
be interested in contributing. \n\
\n\
How could you team up with the Fedora community to use and develop your \
skills?  Check out http://fedoraproject.org/wiki/Join for some ideas. \
Our community is more than just software developers -- we also have a \
place for you whether you're an artist, a web site builder, a writer, or \
a people person.  You'll grow and learn as you work on a team with other \
very smart and talented people. \n\
\n\
Fedora and FOSS are changing the world -- come be a part of it!") % {'name': user.givenName, 'email': user.mail}
            turbomail.enqueue(message)
            turbogears.flash(_('Message sent to: %s') % target)
        return dict(target=target, user=user)

def relativeUser(realUser, sudoUser):
    ''' Takes user and sees if they are allow to sudo for remote group'''
    p = Person.byUserName('realUser')
