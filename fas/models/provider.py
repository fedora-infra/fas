# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy import func

from fas.models import MembershipStatus
from fas.models import DBSession as session

from fas.models.la import (
    LicenseAgreement,
    SignedLicenseAgreement
    )

from fas.models.configs import AccountPermissions

from fas.models.group import (
    Groups,
    GroupType,
    GroupMembership
    )

from fas.models.people import (
    People,
    PeopleAccountActivitiesLog
    )


def __get_listoffset(page, limit):
    """ Get offset based on requeted limit. """
    offset = (page - 1) * limit

    if offset < limit:
        offset = -1
    else:
        offset += 1

    return offset


# Method to get AccountStatus

# Disable retrieval of account's status from database as we disabled
# dynamic account's status.

#def get_accountstatus():
    #""" Retrieve all the status an account can have. """
    #query = session.query(AccountStatus)
    #return query.all()

# Same as above.
#def get_accountstatus_by_status(status):
    #""" Retrieve the status an account can have for the specified status.
    #"""
    #query = session.query(
        #AccountStatus
    #).filter(
        #sa.func.lower(AccountStatus.status) == sa.func.lower(status)
    #)
    #return query.first()


# Method to get RoleLevel

# Disabled function. see above for details
#.
#def get_role_levels():
    #""" Retrieve all the roles someone can have in a group. """
    #query = session.query(RoleLevel)
    #return query.all()


# Method to interact with Groups

def get_groups_count():
    """ Retrieve number of registered groups and returns its value. """
    return session.query(func.count(Groups.id)).first()[0]


def get_groups(limit=None, page=None):
    """ Retrieve all registered groups from databse. """
    if limit and page:
        query = session.query(Groups) \
            .limit(limit) \
            .offset(__get_listoffset(page, limit))
    else:
        query = session.query(Groups)

    return query.all()


def get_candidate_parent_groups():
    """ Retrieve all groups that can be a parent group."""
    query = session.query(Groups.id, Groups.name)\
        .filter(Groups.parent_group_id == -1)\
        .order_by(Groups.name)
    return query.all()


def get_child_groups():
    """ Retrieve all child groups."""
    query = session.query(Groups).filter(Groups.parent_group_id >= -1)
    return query.all()



def get_group_by_id(id):
    """ Retrieve Groups by its id. """
    query = session.query(Groups).filter(Groups.id == id)
    return query.first()


def get_group_by_name(name):
    """ Retrieve Groups by its name.

    :name: Group name.
    :return: Group object
    """
    query = session.query(Groups).filter(Groups.name == name)
    return query.first()


def get_group_membership(id):
    """ Retrieve group's membership by group's id

    :id: Group id
    :return: Tuple of related group, membership, people and roles object
             for a given group's id
    """
    query = session.query(
        Groups, GroupMembership, People,
    ).join(
        (GroupMembership, GroupMembership.group_id == Groups.id)
    ).join(
        People, People.id == GroupMembership.people_id
    ).filter(
        Groups.id == id
    )

    return query.all()


def get_group_by_people_membership(username):
    """ Retrieve groups based on membership by people's username.

    :username: people username
    :return: List of groups object related to username's membership.
    """
    query = session.query(
        Groups
    ).join(
        (GroupMembership, GroupMembership.group_id == Groups.id)
    ).join(
        People, People.username == username
    ).filter(
        GroupMembership.people_id == People.id
    )

    return query.all()


def get_membership(username, group):
    """ Retrieve membership from given username and group name.

    :username: people username
    :group: Group name
    :return: Membership object
    """
    query = session.query(
        GroupMembership
    ).join(
        People, People.username == username
    ).join(
        Groups, Groups.name == group
    ).filter(
        GroupMembership.people_id == People.id,
        GroupMembership.group_id == Groups.id
    )

    return query.first()


def get_membership_by_role(group, person, role):
    """ Retrieve group membership request from given group and person

    :param group:`fas.models.group.Groups.id`
    :type group: integer
    :param person: `fas.models.people.People.id`
    :type person: list(`fas.models.group.GroupMembership`)
    """
    query = session.query(
        GroupMembership
    ).filter(
        GroupMembership.group_id == group,
        GroupMembership.people_id == person,
        GroupMembership.role == role
    )

    return query.first()


def get_memberships_by_status(status, group=None):
    """ Retrieve group membership request from given group and status

    :param status: a membership status `fas.models.GroupMembershipStatus`
    :type status: IntEnum
    :param group: a group id, `fas.models.group.Groups.id`
    :type group: integer
    :rtype: `fas.models.group.GroupMembership`
    """
    query = session.query(
        GroupMembership
    ).filter(GroupMembership.status == status)

    if group:
        query = session.query(
        GroupMembership
        ).filter(
            GroupMembership.status == status,
            GroupMembership.group_id == group
            )

    return query.all()


def get_membership_requests(group):
    """ Retrieve group membership request from given group.

    :param group: integer, group id.
    :rtype: :class:`fas.models.group.MembershipRequest`
    """
    query = session.query(
        MembershipRequest
    ).filter(
        MembershipRequest.group_id == group
    )

    return query.all()


def get_membership_request_by_people(people):
    """ Retrieve group membership request from given people

    :param people: integer, people id
    :rtype: :class:`fas.models.group.MembershipRequest`
    """
    query = session.query(MembershipRequest)\
    .filter(MembershipRequest.person_id == People.id)

    return query.all()

# Method to interact with GroupType


def get_group_types():
    """ Retrieve group's types."""
    query = session.query(GroupType)
    return query.all()


def get_grouptype_by_id(id):
    """ Retrive GroupType by its id. """
    query = session.query(GroupType).filter(GroupType.id == id)
    return query.first()


# Method to interact with People

def get_people_count():
    """ Return people count. """
    return session.query(func.count(People.id)).first()[0]


def get_people(limit=None, page=None):
    """ Retrieve all registered people from database. """
    if limit and page:
        query = session.query(
            People
        ).order_by(
            People.username
        ).limit(
            limit
        ).offset(
            __get_listoffset(page, limit)
        )
    else:
        query = session.query(People).order_by(People.username)

    return query.all()


def get_people_username():
    """ Retrieve and return list of tuple of people's username and id."""
    query = session.query(
        People.id, People.username
    ).order_by(
        People.username
    )
    return query.all()


def get_people_by_id(id):
    """ Retrieve People by its id. """
    query = session.query(People).filter(People.id == id)
    return query.first()


def get_people_by_username(username):
    """ Retrieve People by its username. """
    query = session.query(People).filter(People.username == username)
    return query.first()


def get_people_by_password_token(token):
    """ Retrieve People by its password token. """
    query = session.query(People).filter(People.password_token == token)

    return query.first()

def get_authenticated_user(request):
    """ Retrieve authenticated person object."""
    return get_people_by_username(request.authenticated_userid)


def get_people_by_email(email):
    """ Retrieve People by its email. """
    query = session.query(People).filter(People.email == email)
    return query.first()


def get_people_by_ircnick(ircnick):
    """ Retrieve by its ircnick. """
    query = session.query(People).filter(People.ircnick == ircnick)
    return query.first()


def get_account_activities_by_people_id(id):
    """ Retrieve account's avitivities by people's id. """
    query = session.query(
        PeopleAccountActivitiesLog
    ).filter(
        PeopleAccountActivitiesLog.people == id
    )

    return query.all()


def get_licenses():
    """ Retrieve all licenses from database. """
    query = session.query(LicenseAgreement)
    return query.all()


def get_license_by_id(id):
    """ Retrieve license based on given id"""
    query = session.query(
        LicenseAgreement
    ).filter(
        LicenseAgreement.id == id
    )
    return query.first()


def is_license_signed(id, people_id):
    """ check if people has signed given license.

    :id: license id
    :people_id: people id
    :return: True is people_id has signed otherwise, false.
    """
    query = session.query(
        SignedLicenseAgreement
    ).filter(
        SignedLicenseAgreement.people == people_id,
        SignedLicenseAgreement.license == id
    )

    if query.first() is not None:
        return True

    return False


def get_account_permissions_by_people_id(id):
    """ Retrieve account permissions based on given people's id. """
    query = session.query(
        AccountPermissions
    ).filter(
        AccountPermissions.people == id
    )
    return query.all()


def get_account_permissions_by_token(token):
    """ Retrieve account permission based on given people's token. """
    query = session.query(
        AccountPermissions
    ).filter(
        AccountPermissions.token == token
    )
    return query.first()
