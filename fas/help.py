import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

from fas.auth import *

class Help(controllers.Controller):
    help = { 'none' :               ['Error', '<p>We could not find that help item</p>'],
            'user_ircnick' :        ['IRC Nick (Optional)', '<p>IRC Nick is used to identify yourself on irc.freenode.net.  Please register your nick on irc.freenode.net first, then fill this in so people can find you online when they need to</p>'],
            'user_primary_email' :  ['Primary Email (Required)', '<p>This email address should be your prefered email contact and will be used to send various official emails to.  This is also where your @fedoraproject.org email will get forwarded</p>'],
            'user_human_name' :     ['Full Name (Required)', '<p>Your Human Name or "real life" name</p>'],
            'user_gpg_keyid' :      ['GPG Key', '<p>Only required for users signing the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  It is generally used to prove that a message or email came from you or to encrypt information so that only the recipients can read it.  See the <a href="http://fedoraproject.org/wiki/Infrastructure/AccountSystem/CLAHowTo">CLAHowTo</a> for more information</p>'],
            'user_telephone' :      ['Telephone', '<p>Only required for users signing the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  Sometimes during a time of emergency someone from the Fedora Project may need to contact you.  For more information see our <a href="http://fedoraproject.org/wiki/Legal/PrivacyPolicy">Privacy Policy</a></p>'],
            'user_postal_address':  ['Postal Address', '<p>Only required for users signing the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  This should be a mailing address where you can be contacted.  See our <a href="http://fedoraproject.org/wiki/Legal/PrivacyPolicy">Privacy Policy</a> about any concerns.</p>'],
            'user_timezone':        ['Timezone (Optional)', '<p>Please specify the time zone you are in.</p>'],
            'user_comments':        ['Comments (Optional)', '<p>Misc comments about yourself.</p>'],
            'user_account_status':  ['Account Status', '<p>Shows account status, possible values include<ul><li>Valid</li><li>Disabled</li><li>Expired</li></ul></p>'],
            'user_cla' :            ['CLA', '<p>In order to become a full Fedora contributor you must sign a <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">Contributor License Agreement</a>.  This license is a legal agreement between you and Red Hat.  Full status allows people to contribute content and code and is recommended for anyone interested in getting involved in the Fedora Project.  To find out more, see the <a href="http://fedoraproject.org/wiki/Infrastructure/AccountSystem/CLAHowTo">CLAHowTo</a>.</p>'],
            'user_ssh_key' :        ['Public SSH Key', '<p>Many resources require public key authentiaction to work.  By uploading your public key to us, you can then log in to our servers.  Type "man ssh-keygen" for more information on creating your key.  Once created you will want to upload ~/.ssh/id_dsa.pub or ~/.ssh/id_rsa.pub</p>'],
            'user_locale':          ['Locale', '<p>For non-english speaking peoples this allows individuals to select which locale they are in.</p>'],
            
            'group_apply':          ['Apply', '<p>Applying for a group is like applying for a job and it can certainly take a while to get in.  Many groups have their own rules about how to actually get approved or sponsored.  For more information on how the account system works see the <a href="../about">about page</a>.</p>'],
            'group_remove':         ['Remove', '''<p>Removing a person from a group will cause that user to no longer be in the group.  They will need to re-apply to get in.  Admins can remove anyone, Sponsors can remove users, users can't remove anyone.</p>'''],
            'group_upgrade':        ['Upgrade', '''<p>Upgrade a persons status in this group.<ul><li>from user -> to sponsor</li><li>From sponsor -> administrator</li><li>administrators cannot be upgraded beyond administrator</li></ul></p>'''],
            'group_downgrade':      ['Downgrade', '''<p>Downgrade a persons status in the group.<ul><li>from administrator -> to sponsor</li><li>From sponsor -> user</li><li>users cannot be downgraded below user, you may want to remove them</li></ul></p>'''],
            'group_approve':        ['Approve', '''<p>A sponsor or administrator can approve users to be in a group.  Once the user has applied for the group, go to the group's page and click approve to approve the user.</p>'''],
            'group_sponsor':        ['Sponsor', '''<p>A sponsor or administrator can sponsor users to be in a gruop.  Once the user has applied for the group, go to the group's page and click approve to sponsor the user.  Sponsorship of a user implies that you are approving a user and may mentor and answer their questions as they come up.</p>'''],
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
