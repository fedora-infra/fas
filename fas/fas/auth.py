from turbogears import config

from fas.fasLDAP import UserAccount
from fas.fasLDAP import Person
from fas.fasLDAP import Groups
from fas.fasLDAP import UserGroup

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
    # TODO: Allow the group owner to admin a group.
    if not g:
        g = Groups.byUserName(userName)
    try:
        if isAdmin(userName, g) or \
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

def canEditUser(userName, editUserName):
    if userName == editUserName:
        return True
    elif isAdmin(userName):
        return True
    else:
        return False

