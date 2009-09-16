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

import re

from turbogears import config
import turbogears

from sqlalchemy.exceptions import InvalidRequestError

from fas.model import PersonRoles

def isAdmin(person):
    '''
    Returns True if the user is a FAS admin (a member of the admingroup)
    '''
    admingroup = config.get('admingroup')
    try:
        if person.group_roles[admingroup].role_status == 'approved':
            return True
    except KeyError:
        return False
    return False

def canAdminGroup(person, group, role=None):
    '''
    Returns True if the user is allowed to act as an admin for a group
    '''
    if isAdmin(person) or (group.owner == person):
        return True
    if not role:
        try:
            role = PersonRoles.query.filter_by(group=group, member=person).one()
        except InvalidRequestError:
            ''' Not in the group '''
            return False
    if role.role_status == 'approved' and role.role_type == 'administrator':
        return True
    return False

def canSponsorGroup(person, group):
    '''
    Returns True if the user is allowed to act as a sponsor for a group
    '''
    if isAdmin(person) or \
        group.owner == person:
        return True
    try:
        role = PersonRoles.query.filter_by(group=group, member=person).one()
    except InvalidRequestError:
        ''' Not in the group '''
        return False
    if (role.role_status == 'approved' and role.role_type == 'sponsor') \
        or canAdminGroup(person, group, role):
        return True
    return False

def isApproved(person, group):
    '''
    Returns True if the user is an approved member of a group
    '''
    try:
        if person.group_roles[group.name].role_status == 'approved':
            return True
    except KeyError:
        return False
    return False

def CLADone(person):
    '''
    Returns True if the user has completed the CLA
    '''
    cla_done_group = config.get('cla_done_group')
    try:
        if person.group_roles[cla_done_group].role_status == 'approved':
            return True
    except KeyError:
        return False
    return False

def canEditUser(person, target):
    '''
    Returns True if the user has privileges to edit the target user
    '''
    if person == target:
        return True
    elif isAdmin(person):
        return True
    return False

def canCreateGroup(person, group):
    '''
    Returns True if the user can create groups
    '''
    # Should groupname restrictions go here?
    if isAdmin(person):
        return True
    try:
        # isApproved is more appropriate here, but that would require an extra group.by_name.  
        # I need to think over the efficiency of auth.py.  Maybe something in model.py so that
        # Any given query should only be called once...
        if person.group_roles['sysadmin'].role_status == 'approved':
            return True
    except KeyError:
        return False
    return False

def canEditGroup(person, group):
    '''
    Returns True if the user can edit the group
    '''
    if canAdminGroup(person, group):
        return True
    return False

def canViewGroup(person, group):
    '''
    Returns True if the user can view the group
    '''
    # If the group matched by privileged_view_groups, then
    # only people that can admin the group can view it
    privilegedViewGroups = config.get('privileged_view_groups')
    if re.compile(privilegedViewGroups).match(group.name):
        if not canAdminGroup(person, group):
            return False
    return True

def canApplyGroup(person, group, applicant):
    '''
    Returns True if the user can apply applicant to the group
    '''
    # User must satisfy all dependencies to join.
    # This is bypassed for people already in the group and for the
    # owner of the group (when they initially make it).
    prerequisite = group.prerequisite
    # TODO: Make this raise more useful info.
    if prerequisite:
        if prerequisite not in applicant.approved_memberships:
            turbogears.flash(_('%s membership required before application to this group is allowed') % prerequisite.name)
            return False

    # group sponsors can apply anybody.
    if canSponsorGroup(person, group):
        return True

    # TODO: We can implement invite-only groups here instead.
    if person == applicant and group.group_type not in ('system'):
        return True

    return False

def canSponsorUser(person, group, target):
    '''
    Returns True if the user can sponsor target in the group
    '''
    # This is just here in case we want to add more complex checks in the future 
    if canSponsorGroup(person, group):
        return True
    return False

def canRemoveUser(person, group, target):
    '''
    Returns True if the user can remove target from the group
    '''
    # Only administrators can remove administrators.
    if canAdminGroup(target, group) and \
        not canAdminGroup(person, group):
        return False
    # A user can remove themself from a group if user_can_remove is 1
    # Otherwise, a sponsor can remove sponsors/users.
    elif ((person == target) and (group.user_can_remove == True)) or \
        canSponsorGroup(person, group):
        return True
    return False

def canUpgradeUser(person, group, target):
    '''
    Returns True if the user can upgrade target in the group
    '''
    # Group admins can upgrade anybody.
    # The controller should handle the case where the target
    # is already a group admin.
    if canAdminGroup(person, group):
        return True
    return False

def canDowngradeUser(person, group, target):
    '''
    Returns True if the user can downgrade target in the group
    '''
    # Group admins can downgrade anybody.
    if canAdminGroup(person, group):
        return True
    return False

