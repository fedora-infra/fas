import turbogears
from turbogears import controllers, expose, paginate, identity, redirect, widgets, validate, validators, error_handler
from turbogears.database import session

from fas.auth import *

class Help(controllers.Controller):
    help = { 'none' :               [_('Error'), _('<p>We could not find that help item</p>')],
            'user_ircnick' :        [_('IRC Nick (Optional)'), _('<p>IRC Nick is used to identify yourself on irc.freenode.net.  Please register your nick on irc.freenode.net first, then fill this in so people can find you online when they need to</p>')],
            'user_email' :  [_('Email (Required)'), _('<p>This email address should be your prefered email contact and will be used to send various official emails to.  This is also where your @fedoraproject.org email will get forwarded</p>')],
            'user_human_name' :     [_('Full Name (Required)'), _('<p>Your Human Name or "real life" name</p>')],
            'user_gpg_keyid' :      [_('GPG Key'), _('<p>A GPG key is generally used to prove that a message or email came from you or to encrypt information so that only the recipients can read it.  This can be used when a password reset is sent to your email.</p>')],
            'user_telephone' :      [_('Telephone'), _('<p>Required in order to complete the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  Sometimes during a time of emergency someone from the Fedora Project may need to contact you.  For more information see our <a href="http://fedoraproject.org/wiki/Legal/PrivacyPolicy">Privacy Policy</a></p>')],
            'user_postal_address':  [_('Postal Address'), _('<p>Required in order to complete the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  This should be a mailing address where you can be contacted.  See our <a href="http://fedoraproject.org/wiki/Legal/PrivacyPolicy">Privacy Policy</a> about any concerns.</p>')],
            'user_timezone':        [_('Timezone (Optional)'), _('<p>Please specify the time zone you are in.</p>')],
            'user_comments':        [_('Comments (Optional)'), _('<p>Misc comments about yourself.</p>')],
            'user_account_status':  [_('Account Status'), _('<p>Shows account status, possible values include<ul><li>Valid</li><li>Disabled</li><li>Expired</li></ul></p>')],
            'user_cla' :            [_('CLA'), _('<p>In order to become a full Fedora contributor you must complete the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">Contributor License Agreement</a>.  This license is a legal agreement between you and Red Hat.  Full status allows people to contribute content and code and is recommended for anyone interested in getting involved in the Fedora Project.</p>')],
            'user_ssh_key' :        [_('Public SSH Key'), _('<p>Many resources require public key authentiaction to work.  By uploading your public key to us, you can then log in to our servers.  Type "man ssh-keygen" for more information on creating your key.  Once created you will want to upload ~/.ssh/id_dsa.pub or ~/.ssh/id_rsa.pub</p>')],
            'user_locale':          [_('Locale'), _('<p>For non-english speaking peoples this allows individuals to select which locale they are in.</p>')],
            
            'group_apply':          [_('Apply'), _('<p>Applying for a group is like applying for a job and it can certainly take a while to get in.  Many groups have their own rules about how to actually get approved or sponsored.  For more information on how the account system works see the <a href="../about">about page</a>.</p>')],
            'group_remove':         [_('Remove'), _('''<p>Removing a person from a group will cause that user to no longer be in the group.  They will need to re-apply to get in.  Admins can remove anyone, Sponsors can remove users, users can't remove anyone.</p>''')],
            'group_upgrade':        [_('Upgrade'), _('''<p>Upgrade a persons status in this group.<ul><li>from user -> to sponsor</li><li>From sponsor -> administrator</li><li>administrators cannot be upgraded beyond administrator</li></ul></p>''')],
            'group_downgrade':      [_('Downgrade'), _('''<p>Downgrade a persons status in the group.<ul><li>from administrator -> to sponsor</li><li>From sponsor -> user</li><li>users cannot be downgraded below user, you may want to remove them</li></ul></p>''')],
            'group_approve':        [_('Approve'), _('''<p>A sponsor or administrator can approve users to be in a group.  Once the user has applied for the group, go to the group's page and click approve to approve the user.</p>''')],
            'group_sponsor':        [_('Sponsor'), _('''<p>A sponsor or administrator can sponsor users to be in a gruop.  Once the user has applied for the group, go to the group's page and click approve to sponsor the user.  Sponsorship of a user implies that you are approving a user and may mentor and answer their questions as they come up.</p>''')],
            'group_user_add':       [_('Add User'), _('''<p>Manually add a user to a group.  Place their username in this field and click 'Add'</p>''')],
            'group_name':           [_('Group Name'), _('''<p>The name of the group you'd like to create.  It should be alphanumeric though '-'s are allowed</p>''')],
            'group_display_name':   [_('Display Name'), _('''<p>More human readable name of the group</p>''')],
            'group_owner':          [_('Group Owner'), _('''<p>The name of the owner who will run this group</p>''')],
            'group_type':           [_('Group Type'), _('''<p>Normally it is safe to leave this blank.  Though some values include 'tracking', 'shell', 'cvs', 'git', 'hg', 'svn', and 'mtn'.  This value only really matters if the group is to end up getting shell access or commit access somewhere like fedorahosted.</p>''')],
            'group_needs_sponsor':  [_('Needs Sponsor'), _('''<p>If your group requires sponsorship (recommended), this means that when a user is approved by a sponsor.  That relationship is recorded in the account system.  If user A sponsors user N, then in viewing the members of this group, people will know to contact user A about user N if something goes wrong.  If this box is unchecked, this means that only approval is needed and no relationship is recorded about who did the approving</p>''')],
            'group_self_removal':   [_('Self Removal'), _('''<p>Should users be able to remove themselves from this group without sponsor / admin intervention?  (recommended yes)</p>''')],
            'group_prerequisite':   [_('Must Belong To'), _('''<p>Before a user can join this group, they must belong to the group listed in this box.  <b>This value cannot be removed without administrative intervention, only changed</b>.  Recommended values are for the 'cla_done' group.</p>''')],
            'group_join_message':   [_('Join Message'), _('''<p>This message will go out to users when they join the group.  It should be informative and offer tips about what to do next.  A description of the group would also be valuable here</p>''')],
            'gencert':              [_('Client Side Cert'), _('''<p>The client side cert is generally used to grant access to upload packages to Fedora or for other authentication purposes like with koji.  If you are not a package maintainer there is no need to worry about the client side cert</p>''')],
            }

    def __init__(self):
        '''Create a JsonRequest Controller.'''

    @expose(template="fas.templates.help")
    def get_help(self, id='none'):
        try:
            helpItem = self.help[id]
        except KeyError:
            return dict(title=_('Error'), helpItem=[_('Error'), _('<p>We could not find that help item</p>')])
        return dict(help=helpItem)
