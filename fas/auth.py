from turbogears import config

from fas.model import Groups
from fas.model import PersonRoles
from fas.model import People

from sqlalchemy.exceptions import *
import turbogears

import re

def isAdmin(person):
    '''
    Returns True if the user is a FAS admin (a member of the admingroup)
    '''
    admingroup = config.get('admingroup')
    try:
        if person.group_roles[admingroup].role_status == 'approved':
            return True
        else:
            return False
    except KeyError:
        return False
    return False
    
def canAdminGroup(person, group):
    '''
    Returns True if the user is allowed to act as an admin for a group
    '''
    if isAdmin(person) or (group.owner == person):
        return True
    else:
        try:
            role = PersonRoles.query.filter_by(group=group, member=person).one()
        except IndexError:
            ''' Not in the group '''
            return False
        except InvalidRequestError:
            return False
        if role.role_status == 'approved' and role.role_type == 'administrator':
            return True
    return False

def canSponsorGroup(person, group):
    '''
    Returns True if the user is allowed to act as a sponsor for a group
    '''
    try:
        if isAdmin(person) or \
            group.owner == person:
            return True
        else:
            try:
                role = PersonRoles.query.filter_by(group=group, member=person).one()
            except IndexError:
                ''' Not in the group '''
                return False
            if role.role_status == 'approved' and role.role_type == 'sponsor':
                return True
        return False
    except:
        return False

def isApproved(person, group):
    '''
    Returns True if the user is an approved member of a group
    '''
    try:
        if person.group_roles[group.name].role_status == 'approved':
            return True
        else:
            return False
    except KeyError:
        return False
    return False

def CLADone(person):
    '''
    Returns True if the user has completed the CLA
    '''
    cla_done_group =config.get('cla_done_group')
    try:
        if person.group_roles[cla_done_group].role_status == 'approved':
            return True
        else:
            return False
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
    else:
        return False

def canCreateGroup(person, group):
    '''
    Returns True if the user can create groups
    '''
    # Should groupname restrictions go here?
    if isAdmin(person):
        return True
    else:
        return False

def canEditGroup(person, group):
    '''
    Returns True if the user can edit the group
    '''
    if canAdminGroup(person, group):
        return True
    else:
        return False

def canViewGroup(person, group):
    '''
    Returns True if the user can view the group
    '''
    # If the group matched by privileged_view_groups, then
    # only people that can admin the group can view it
    privilegedViewGroups = config.get('privileged_view_groups')
    if re.compile(privilegedViewGroups).match(group.name):
        if canAdminGroup(person, group):
            return True
        else:
            return False
    else:
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
    # A user can apply themselves, and group sponsors can apply other people.
    if (person == applicant) or \
        canSponsorGroup(person, group):
        return True
    else:
        turbogears.flash(_('%s membership required before application to this group is allowed') % prerequisite.name)
        return False

def canSponsorUser(person, group, target):
    '''
    Returns True if the user can sponsor target in the group
    '''
    # This is just here in case we want to add more complex checks in the future 
    if canSponsorGroup(person, group):
        return True
    else:
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
    else:
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
    # Sponsors can only upgrade non-sponsors (i.e. normal users)
    # TODO: Don't assume that canSponsorGroup means that the user is a sponsor
    elif canSponsorGroup(person, group) and \
        not canSponsorGroup(target, group):
        return True
    else:
        return False

def canDowngradeUser(person, group, target):
    '''
    Returns True if the user can downgrade target in the group
    '''
    # Group admins can downgrade anybody.
    if canAdminGroup(person, group):
        return True
    # Sponsors can only downgrade sponsors.  
    # The controller should handle the case where the target
    # is already a normal user.  
    elif canSponsorGroup(person, group) and \
        not canAdminGroup(person, group):
        return True
    else:
        return False

