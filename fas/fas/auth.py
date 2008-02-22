from turbogears import config

#from fas.fasLDAP import UserAccount
#from fas.fasLDAP import Person
#from fas.fasLDAP import Groups
#from fas.fasLDAP import UserGroup

from fas.model import Groups
from fas.model import PersonRoles
from fas.model import People

from sqlalchemy.exceptions import *
import re

def isAdmin(username):
    '''
    Returns True if the user is a FAS admin (a member of the admingroup)
    '''
    p = People.by_username(username)
    admingroup = config.get('admingroup')
    try:
        g = Groups.by_name(admingroup)
    except InvalidRequestError:
        print '%s - Your admin group could not be found!' % admingroup
        return False
    if g in p.approved_memberships:
        return True
    else:
        return False
    
def canAdminGroup(username, groupname):
    '''
    Returns True if the user is allowed to act as an admin for a group
    '''
    g = Groups.by_name(groupname)
    p = People.by_username(username)
    try:
        if isAdmin(username) or (g.owner == p):
            return True
        else:
            try:
                r = PersonRoles.query.filter_by(group_id=g.id, person_id=p.id).one()
            except IndexError:
                ''' Not in the group '''
                return False
            if r.role_status == 'approved' and r.role_type == 'administrator':
                return True
        return False
    except:
        return False

def canSponsorGroup(username, groupname):
    '''
    Returns True if the user is allowed to act as a sponsor for a group
    '''
    p = People.by_username(username)
    print "GROUPNAME %s " % groupname
    g = Groups.by_name(groupname)
    try:
        if isAdmin(username, g) or \
            g.owner == p:
            return True
        else:
            try:
                r = PersonRoles.query.filter_by(group_id=g.id, person_id=p.id).one()
            except IndexError:
                ''' Not in the group '''
                return False
            if r.role_status == 'approved' and r.role_type == 'sponsor':
                return True
        return False
    except:
        return False
def isApproved(username, groupname):
    '''
    Returns True if the user is an approved member of a group
    '''
    g = Groups.by_name(groupname)
    try:
        r = PersonRoles.query.filter_by(group_id=g.id, person_id=p.id).one()
    except IndexError:
        ''' Not in the group '''
        return False
    if r.role_status == 'approved':
        return True
    else:
        return False

def signedCLAPrivs(username):
    '''
    Returns True if the user has completed the GPG-signed CLA
    '''
    if isApproved(username, config.get('cla_sign_group')):
        return True
    else:
        return False

def clickedCLAPrivs(username):
    '''
    Returns True if the user has completed the click-through CLA
    '''
    if signedCLAPrivs(username) or \
       isApproved(username, config.get('cla_click_group')):
        return True
    else:
        return False

def canEditUser(username, target):
    '''
    Returns True if the user has privileges to edit the target user
    '''
    if username == target:
        return True
    elif isAdmin(username):
        return True
    else:
        return False

def canCreateGroup(username, groupname):
    '''
    Returns True if the user can create groups
    '''
    # Should groupname restrictions go here?
    if isAdmin(username):
        return True
    else:
        return False

def canEditGroup(username, groupname):
    '''
    Returns True if the user can edit the group
    '''
    if canAdminGroup(username, groupname):
        return True
    else:
        return False

def canViewGroup(username, groupname):
    '''
    Returns True if the user can view the group
    '''
    # If the group matched by privileged_view_groups, then
    # only people that can admin the group can view it
    privilegedViewGroups = config.get('privileged_view_groups')
    if re.compile(privilegedViewGroups).match(groupname):
        if canAdminGroup(username, groupname):
            return True
        else:
            return False
    else:
        return True

def canApplyGroup(username, groupname, applicant):
    '''
    Returns True if the user can apply applicant to the group
    '''
    # User must satisfy all dependencies to join.
    # This is bypassed for people already in the group and for the
    # owner of the group (when they initially make it).
    p = People.by_username(username)
    prerequisite = group.prerequisite
    if prequisite:
        if prerequisite in p.approved_memberships:
            pass
        else:
            return False
    # A user can apply themselves, and FAS admins can apply other people.
    if (username == applicant) or \
        canAdminGroup(username, groupname):
        return True
    else:
        return False

def canSponsorUser(username, groupname, target):
    '''
    Returns True if the user can sponsor target in the group
    '''
    # This is just here in case we want to add more complex checks in the future 
    if canSponsorGroup(username, groupname):
        return True
    else:
        return False

def canRemoveUser(username, groupname, target):
    '''
    Returns True if the user can remove target from the group
    '''
    group = Groups.by_name(groupname)
    # Only administrators can remove administrators.
    if canAdminGroup(target, groupname) and \
        not canAdminGroup(username, groupname):
        return False
    # A user can remove themself from a group if user_can_remove is 1
    # Otherwise, a sponsor can remove sponsors/users.
    elif ((username == target) and (group.user_can_remove == 1)) or \
        canSponsorGroup(username, groupname, g):
        return True
    else:
        return False

def canUpgradeUser(username, groupname, target):
    '''
    Returns True if the user can upgrade target in the group
    '''
    if isApproved(username, groupname):
        # Group admins can upgrade anybody.
        # The controller should handle the case where the target
        # is already a group admin.
        if canAdminGroup(username, groupname):
            return True
        # Sponsors can only upgrade non-sponsors (i.e. normal users)
        elif canSponsorGroup(username, groupname) and \
            not canSponsorGroup(target, groupname):
            return True
        else:
            return False
    else:
        return False

def canDowngradeUser(username, groupname, target):
    '''
    Returns True if the user can downgrade target in the group
    '''
    # Group admins can downgrade anybody.
    if canAdminGroup(username, groupname):
        return True
    # Sponsors can only downgrade sponsors.  
    # The controller should handle the case where the target
    # is already a normal user.  
    elif canSponsorGroup(username, groupname) and \
        not canAdminGroup(target, groupname):
        return True
    else:
        return False

