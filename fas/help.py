import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

from fas.auth import *

class Help(controllers.Controller):
    help = { 'none' :      ['Error', '<p>We could not find that help item</p>'],
            'user_ircnick' :       ['IRC Nick (Optional)', '<p>IRC Nick is used to identify yourself on irc.freenode.net.  Please register your nick on irc.freenode.net first, then fill this in so people can find you online when they need to</p>'],
            'user_primary_email' : ['Primary Email (Required)', '<p>This email address should be your prefered email contact and will be used to send various official emails to.  This is also where your @fedoraproject.org email will get forwarded</p>'],
            'user_human_name' :    ['Full Name (Required)', '<p>Your Human Name or "real life" name</p>'],
            'user_gpg_keyid' :     ['GPG Key', '<p>Only required for users signing the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  It is generally used to prove that a message or email came from you or to encrypt information so that only the recipients can read it.  See the <a href="http://fedoraproject.org/wiki/Infrastructure/AccountSystem/CLAHowTo">CLAHowTo</a> for more information</p>'],
            'user_telephone' :     ['Telephone', '<p>Only required for users signing the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  Sometimes during a time of emergency someone from the Fedora Project may need to contact you.  For more information see our <a href="http://fedoraproject.org/wiki/Legal/PrivacyPolicy">Privacy Policy</a></p>'],
            }

    def __init__(self):
        '''Create a JsonRequest Controller.'''

    @expose(template="fas.templates.help")
    def get_help(self, id='none'):
        try:
            helpItem = self.help[id]
        except KeyError:
            return dict(title='Error', helpItem=['Error', '<p>We could not find that help item</p>'])
        return dict(help=helpItem)
