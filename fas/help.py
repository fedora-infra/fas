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
from turbogears import controllers, expose

class Help(controllers.Controller):
    help = { 'none' :               [_('Error'), _('<p>We could not find that help item</p>')],
            'cla_accuracy': [_('Accuracy of CLA Information'), _('<p>The CLA is a legal document.  We need to have accurate information attached to it just in case we ever need to contact you about a contribution that you make to the project.  Imagine if we were to get a call from a lawyer at some other company claiming that they own the copyright to your work and we have to tell them we have a right to use it because "Mickey Moose" contributed it to us and we have no telephone number to contact them!  Potentially a very sticky situation.</p>')],
            'user_ircnick' :        [_('IRC Nick (Optional)'), _('<p>IRC Nick is used to identify yourself on irc.freenode.net.  Please register your nick on irc.freenode.net first, then fill this in so people can find you online when they need to</p>')],
            'user_email' :  [_('Email (Required)'), _('<p>This email address should be your prefered email contact and will be used to send various official emails to.  This is also where your @fedoraproject.org email will get forwarded</p>')],
            'user_human_name' :     [_('Full Name (Required)'), _('<p>Your Human Name or "real life" name</p>')],
            'user_gpg_keyid' :      [_('GPG Key ID'), _('<p>A GPG key is generally used to prove that a message or email came from you or to encrypt information so that only the recipients can read it.  This can be used when a password reset is sent to your email.</p>')],
            'user_telephone' :      [_('Telephone'), _('<p>Required in order to complete the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  Sometimes during a time of emergency someone from the Fedora Project may need to contact you.  For more information see our <a href="http://fedoraproject.org/wiki/Legal/PrivacyPolicy">Privacy Policy</a></p>')],
            'user_postal_address':  [_('Postal Address'), _('<p>This should be a mailing address where you can be contacted.  See our <a href="http://fedoraproject.org/wiki/Legal/PrivacyPolicy">Privacy Policy</a> about any concerns.</p>')],
            'user_timezone':        [_('Timezone (Optional)'), _('<p>Please specify the time zone you are in.</p>')],
            'user_comments':        [_('Comments (Optional)'), _('<p>Misc comments about yourself.</p>')],
            'user_account_status':  [_('Account Status'), _('<p>Shows account status, possible values include<ul><li>active</li><li>vacation</li><li>inactive</li></ul></p>')],
            'user_cla' :            [_('CLA'), _('<p>In order to become a full Fedora contributor you must complete the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">Contributor License Agreement</a>.  This license is a legal agreement between you and Red Hat.  Full status allows people to contribute content and code and is recommended for anyone interested in getting involved in the Fedora Project.</p>')],
            'user_ssh_key' :        [_('Public RSA SSH Key'), _('<p>Many resources require public key authentiaction to work.  By uploading your public key to us, you can then log in to our servers.  Type "man ssh-keygen" for more information on creating your key (it must be an RSA key).  Once created you will want to upload ~/.ssh/id_rsa.pub</p>')],
            'user_locale':          [_('Locale'), _('<p>For non-english speaking peoples this allows individuals to select which locale they are in.</p>')],
            'user_country_code' :   [_('Country Code'), _('<p>Required in order to complete the <a href="http://fedoraproject.org/wiki/Legal/Licenses/CLA">CLA</a>.  Sometimes during a time of emergency someone from the Fedora Project may need to contact you.  For more information see our <a href="http://fedoraproject.org/wiki/Legal/PrivacyPolicy">Privacy Policy</a></p>')],
            'user_age_check':       [_('Must be over 13 Years'), _("<p>Out of special concern for children's privacy, we do not knowingly accept online personal information from children under the age of 13. We do not knowingly allow children under the age of 13 to become registered members of our sites or buy products and services on our sites. We do not knowingly collect or solicit personal information about children under 13.</p>")],
            'user_privacy':         [_('Hide Information'), _("<p>In accordance with our privacy policy, you can choose to hide some of the information given on this page from other people.  Please see the privacy policy for complete details.</p>")],
            'group_apply':          [_('Apply'), _('<p>Applying for a group is like applying for a job and it can certainly take a while to get in.  Many groups have their own rules about how to actually get approved or sponsored.  For more information on how the account system works see the <a href="%s">about page</a>.</p>') % turbogears.url('/about')],
            'group_remove':         [_('Remove'), _('''<p>Removing a person from a group will cause that user to no longer be in the group.  They will need to re-apply to get in.  Admins can remove anyone, Sponsors can remove users, users can't remove anyone.</p>''')],
            'group_upgrade':        [_('Upgrade'), _('''<p>Upgrade a persons status in this group.<ul><li>from user -> to sponsor</li><li>From sponsor -> administrator</li><li>administrators cannot be upgraded beyond administrator</li></ul></p>''')],
            'group_downgrade':      [_('Downgrade'), _('''<p>Downgrade a persons status in the group.<ul><li>from administrator -> to sponsor</li><li>From sponsor -> user</li><li>users cannot be downgraded below user, you may want to remove them</li></ul></p>''')],
            'group_approve':        [_('Approve'), _('''<p>A sponsor or administrator can approve users to be in a group.  Once the user has applied for the group, go to the group's page and click approve to approve the user.</p>''')],
            'group_sponsor':        [_('Sponsor'), _('''<p>A sponsor or administrator can sponsor users to be in a gruop.  Once the user has applied for the group, go to the group's page and click approve to sponsor the user.  Sponsorship of a user implies that you are approving a user and may mentor and answer their questions as they come up.</p>''')],
            'group_user_add':       [_('Add User'), _('''<p>Manually add a user to a group.  Place their username in this field and click 'Add'</p>''')],
            'group_name':           [_('Group Name'), _('''<p>The name of the group you'd like to create.  It should be lowercase alphanumeric though '-' and '_' are allowed</p>''')],
            'group_display_name':   [_('Display Name'), _('''<p>More human readable name of the group</p>''')],
            'group_owner':          [_('Group Owner'), _('''<p>The name of the owner who will run this group</p>''')],
            'group_type':           [_('Group Type'), _('''<p>Normally it is safe to leave this blank.  Though some values include 'tracking', 'shell', 'cvs', 'git', 'hg', 'svn', and 'mtn'.  This value only really matters if the group is to end up getting shell access or commit access somewhere like fedorahosted.</p>''')],
            'group_url':            [_('Group URL (Optional)'), _('''<p>A URL or wiki page for the group (for example, <a href="https://fedoraproject.org/wiki/Infrastructure">https://fedoraproject.org/wiki/Infrastructure</a>).</p>''')],
            'group_mailing_list':     [_('Group Mailing List (Optional)'), _('''<p>A mailing list for the group (for example, fedora-infrastructure-list@redhat.com).</p>''')],
            'group_mailing_list_url': [_('Group Mailing List URL (Optional)'), _('''<p>A URL for the group's mailing list (for example, <a href="http://www.redhat.com/mailman/listinfo/fedora-infrastructure-list">http://www.redhat.com/mailman/listinfo/fedora-infrastructure-list</a>).</p>''')],
            'group_invite_only': [_('Invite Only'), _('''<p>If users should not normally be able to apply to the group, setting this will hide the usual "Apply!" links and buttons.  Users can still be added to a group directly by an admin or sponsor.</p>''')],
            'group_irc_channel': [_('Group IRC Channel (Optional)'), _('''<p>An IRC channel for the group (for example, #fedora-admin).</p>''')],
            'group_irc_network': [_('Group IRC Network (Optional)'), _('''<p>The IRC Network for the group's IRC channel (for example, Freenode).</p>''')],
            'group_needs_sponsor':  [_('Needs Sponsor'), _('''<p>If your group requires sponsorship (recommended), this means that when a user is approved by a sponsor.  That relationship is recorded in the account system.  If user A sponsors user N, then in viewing the members of this group, people will know to contact user A about user N if something goes wrong.  If this box is unchecked, this means that only approval is needed and no relationship is recorded about who did the approving</p>''')],
            'group_self_removal':   [_('Self Removal'), _('''<p>Should users be able to remove themselves from this group without sponsor / admin intervention?  (recommended yes)</p>''')],
            'group_prerequisite':   [_('Must Belong To'), _('''<p>Before a user can join this group, they must belong to the group listed in this box.  Recommended values are for the 'cla_done' group.</p>''')],
            'group_join_message':   [_('Join Message'), _('''<p>This message will go out to users when they apply to the group.  It should be informative and offer tips about what to do next.  A description of the group would also be valuable here</p>''')],
            'gencert':              [_('Client Side Cert'), _('''<p>The client side cert is generally used to grant access to upload packages to Fedora or for other authentication purposes like with koji.  You should save this certificate to ~/.fedora.cert.  If you are not a package maintainer there is no need to worry about the client side cert.  Please note that whenever a new cert is generated, all old ones are revoked.</p>''')],
            'latitude_and_longitude':              [_('Longitude and Latitude'), _('''<p>Your longitude and latitude.  This optional field should be entered as a floating point number.  For instance, 312.333 or -21.2.  This may be used for mapping purposes, but will not be used if you have privacy enabled for your account.</p>''')],
            'apply_rules_message':              [_('Rules for Application'), _('''<p>Rules or steps that applicants should follow before appliying to your group.  This will be shown to users before they apply to your group.</p>''')],
            }

    def __init__(self):
        '''Create a JsonRequest Controller.'''

    @expose(template="fas.templates.help")
    def get_help(self, helpid='none'):
        try:
            helpItem = self.help[helpid]
        except KeyError:
            return dict(title=_('Error'), helpItem=[_('Error'), _('<p>We could not find that help item</p>')])
        # Transform to unicode as that's what genshi expects, not lazystring
        helpitem = [unicode(s) for s in helpItem]
        return dict(help=helpItem)
