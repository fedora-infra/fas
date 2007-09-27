from turbogears import config

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

import re

def isAdmin(userName, g=None):
    admingroup = config.get('admingroup')
    if not g:
        g = Groups.byUserName(userName)
    try:
        g[admingroup].cn
        return True
    except KeyError:
        return False
    
def canAdminGroup(userName, groupName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    group = Groups.groups(groupName)[groupName]
    try:
        if isAdmin(userName, g) or \
            (group.fedoraGroupOwner == userName) or \
           (g[groupName].fedoraRoleType.lower() == 'administrator'):
           return True
        else:
           return False
    except:
        return False

def canSponsorGroup(userName, groupName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    try:
        if isAdmin(userName, g) or \
           canAdminGroup(userName, groupName, g) or \
           (g[groupName].fedoraRoleType.lower() == 'sponsor'):
           return True
        else:
           return False
    except:
        return False

def isApproved(userName, groupName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    try:
        if (g[groupName].fedoraRoleStatus.lower() == 'approved'):
           return True
        else:
           return False
    except:
        return False

def signedCLAPrivs(userName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    if isApproved(userName, config.get('cla_sign_group'), g):
        return True
    else:
        return False

def clickedCLAPrivs(userName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    if signedCLAPrivs(userName, g) or \
       isApproved(userName, config.get('cla_click_group'), g):
        return True
    else:
        return False

def canEditUser(userName, editUserName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    if userName == editUserName:
        return True
    elif isAdmin(userName, g):
        return True
    else:
        return False

def canCreateGroup(userName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    if isAdmin(userName, g):
        return True
    else:
        return False

def canEditGroup(userName, groupName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    if canAdminGroup(userName, groupName):
        return True
    else:
        return False

def canViewGroup(userName, groupName, g=None):
    # If the group matched by privileged_view_groups, then
    # only people that can admin the group can view it
    privilegedViewGroups = config.get('privileged_view_groups')
    if re.compile(privilegedViewGroups).match(groupName):
        if not g:
            g = Groups.byUserName(userName)
        if canAdminGroup(userName, groupName, g):
            return True
        else:
            return False
    else:
        return True

def canApplyGroup(userName, groupName, applyUserName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    # User must satisfy all dependencies to join.
    # This is bypassed for people already in the group and for the
    # owner of the group (when they initially make it).
    group = Groups.groups(groupName)[groupName]
    requirements = group.fedoraGroupRequires.split()
    for req in requirements:
        try:
            g[req].cn
        except KeyError:
            return False
    # A user can apply themselves, and FAS admins can apply other people.
    if (userName == applyUserName) or \
        isAdmin(userName, g):
        return True
    else:
        return False

def canSponsorUser(userName, groupName, sponsorUserName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    # This is just here in case we want to add more complex checks in the future 
    if canSponsorGroup(userName, groupName, g):
        return True
    else:
        return False

def canRemoveUser(userName, groupName, removeUserName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    group = Groups.groups(groupName)[groupName]
    # Only administrators can remove administrators.
    if canAdminGroup(removeUserName, groupName) and \
        not canAdminGroup(userName, groupName, g):
        return False
    # A user can remove themself from a group if fedoraGroupUserCanRemove is TRUE
    # Otherwise, a sponsor can remove sponsors/users.
    elif ((userName == removeUserName) and (group.fedoraGroupUserCanRemove.lower() == 'TRUE')) or \
        canSponsorGroup(userName, groupName, g):
        return True
    else:
        return False

def canUpgradeUser(userName, groupName, sponsorUserName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    # Group admins can upgrade anybody (fasLDAP.py has the checks to prevent
    # upgrading admins, etc.
    if canAdminGroup(userName, groupName, g):
        return True
    # Sponsors can only upgrade non-sponsors (i.e. normal users) fasLDAP.py
    # ensures that sponsorUserName is at least an approved user.
    elif canSponsorGroup(userName, groupName, g) and \
        not canSponsorGroup(sponsorUserName, groupName):
        return True
    else:
        return False

def canDowngradeUser(userName, groupName, sponsorUserName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    # Group admins can downgrade anybody.
    if canAdminGroup(userName, groupName, g):
        return True
    # Sponsors can only downgrade sponsors.  (fasLDAP.py won't let you
    # downgrade a normal user already)
    elif canSponsorGroup(userName, groupName, g) and \
        not canAdminGroup(sponsorUserName, groupName):
        return True
    else:
        return False
