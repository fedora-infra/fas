from turbogears import config

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

import re

ADMINGROUP = config.get('admingroup')

def isAdmin(userName, g=None):
    if not g:
        g = Groups.byUserName(userName)
    try:
        g[ADMINGROUP].cn
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
        if canAdminGroup(userName, groupName):
            return True
        else:
            return False
    else:
        return True

def canApplyGroup(userName, groupName, applyUserName, g=None):
    # This is where we could make groups depend on other ones.
    if not g:
        g = Groups.byUserName(userName)
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
