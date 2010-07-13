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
from fas import release
__version__ = release.VERSION

import gettext
translation = gettext.translation('fas', '/usr/share/locale',
                fallback=True)
_ = translation.ugettext

SHARE_CC_GROUP = 'share_country_code'
SHARE_LOC_GROUP = 'share_location'

class FASError(Exception):
    '''FAS Error'''
    pass

class ApplyError(FASError):
    '''Raised when a user could not apply to a group'''
    pass

class ApproveError(FASError):
    '''Raised when a user could not be approved in a group'''
    pass

class SponsorError(FASError):
    '''Raised when a user could not be sponsored in a group'''
    pass

class UpgradeError(FASError):
    '''Raised when a user could not be upgraded in a group'''
    pass

class DowngradeError(FASError):
    '''Raised when a user could not be downgraded in a group'''
    pass

class RemoveError(FASError):
    '''Raised when a user could not be removed from a group'''
    pass
