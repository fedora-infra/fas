import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

from fas.auth import *

class Help(controllers.Controller):
    def __init__(self):
        '''Create a JsonRequest Controller.'''

    @expose(template="fas.templates.help")
    def get_help(self, id='none'):
        try:
            help = { 'none' :      ['Error', 'We could not find that help item'],
            'user_ircnick' :       ['IRC Nick (Optional)', 'IRC Nick is used to identify yourself on irc.freenode.net.  Please register your nick on irc.freenode.net first, then fill this in so people can find you online when they need to'],
            'user_primary_email' : ['Primary Email (Required)', 'This email address should be your prefered email contact and will be used to send various official emails to.  This is also where your @fedoraproject.org email will get forwarded'],
            'user_human_name' :    ['Full Name (Required)', 'Your Human Name or "real life" name'],
            'user_gpg_keyid' :     ['GPG Key', 'Only required for users signing the CLA.  It is generally used to prove that a message or email came from you or to encrypt information so that only the recipients can read it.  See http://fedoraproject.org/wiki/Infrastructure/AccountSystem/CLAHowTo for more information'],
            'user_telephone' :     ['Telephone', 'Only required for users signing the CLA.  Sometimes during a time of emergency someone from the Fedora Project may need to contact you.  For more information see our Privacy Policy'], 
            }
        except KeyError:
            return dict(title='Error', help='We could not find that help item')
        return dict(help=help[id])

