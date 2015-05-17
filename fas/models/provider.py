# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Xavier Lamien.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

from sqlalchemy.sql import or_
from pyramid.security import unauthenticated_userid

from fas.models import MembershipStatus
from fas.models import DBSession as session
from fas.models import AccountStatus
from fas.models import GroupStatus
from fas.models.la import (
    LicenseAgreement,
    SignedLicenseAgreement
    )
from fas.models.configs import AccountPermissions, TrustedPermissions
from fas.models.group import (
    Groups,
    GroupType,
    GroupMembership
    )
from fas.models.people import (
    People,
    PeopleAccountActivitiesLog
    )
from fas.models.certificates import (
    Certificates,
    ClientsCertificates
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
def get_groups(limit=None, page=None, pattern=None, count=False, status=None):
    """ Retrieve all registered groups from databse. """
    if page <= 0:
        page = 1

    query = session.query(Groups)

    if status is not None:
        query = query.filter(Groups.status.in_(status))
    else:
        query = query.filter(
            Groups.status.in_([
                GroupStatus.ACTIVE,
                GroupStatus.INACTIVE]
                ))

    if pattern:
        if '%' in pattern:
            query = query.filter(
                or_(
                    Groups.name.ilike(pattern),
                    Groups.display_name.ilike(pattern)
                )
            )
        else:
            query = query.filter(
                or_(
                    Groups.name == pattern,
                    Groups.display_name == pattern,
                )
            )

    if limit and page:
        query = query.limit(limit).offset(__get_listoffset(page, limit))

    if count:
        return query.count()
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
    ).filter(
        Groups.id == GroupMembership.group_id,
        GroupMembership.people_id == People.id,
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
    ).filter(
        GroupMembership.group_id == Groups.id,
        GroupMembership.people_id == People.id,
        GroupMembership.status == MembershipStatus.APPROVED,
        People.username == username,

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
    :param group: a list of group id, [`fas.models.group.Groups.id`]
    :type group: list()
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
            GroupMembership.group_id.in_(group)
            )

    return query.all()


# Method to interact with GroupType


def get_group_types():
    """
    Retrieve group's types.

    :returns: Registered group's types
    :rtype: list of fas.models.group.GroupType
    """
    query = session.query(GroupType)
    return query.all()


def get_grouptype_by_id(id):
    """ Retrive GroupType by its id. """
    query = session.query(GroupType).filter(GroupType.id == id)
    return query.first()


# Method to interact with People

def get_people(limit=None, page=None, pattern=None, count=False, status=-1):
    """
    Retrieve registered people based on given criteria.

    :param limit: limit number to return
    :type limit: int
    :param page: list offset from where to start looking for people
    :type page: int
    :param pattern: could be people username, fullname or ircnick.
    :type pattern: str
    :param count: return or not only a count from given criteria
    :type count: bool
    :param status: filter people by status
    :type status: fas.models.AccountStatus
    :rtype: list of fas.models.people.People or int
    """
    if page <= 0:
        page = 1

    query = session.query(People).order_by(People.fullname)

    if status > -1:
        query = query.filter(People.status.in_([AccountStatus(status)]))
    else:
        query = query.filter(
            People.status.in_([
                AccountStatus.ACTIVE,
                AccountStatus.ON_VACATION,
                AccountStatus.INACTIVE]
                ))

    if pattern:
        if '%' in pattern:
            query = query.filter(
                or_(
                    People.username.ilike(pattern),
                    People.fullname.ilike(pattern),
                    People.ircnick.ilike(pattern),
                )
            )
        else:
            query = query.filter(
                or_(
                    People.username == pattern,
                    People.fullname == pattern,
                    People.ircnick == pattern,
                )
            )

    if limit and page:
        query = query.limit(
            limit
        ).offset(
            __get_listoffset(page, limit)
        )

    if count:
        return query.count()

    return query.distinct().all()


def get_people_username(filter_out=None):
    """ Retrieve and return people's username.

    :rtype : object
    :param filter_out:
    """
    query = session.query(People.username).filter(People.username != filter_out)

    return query.all()


def get_people_email(filter_username=None):
    """ Retrieve and return registered emails. """
    if filter_username:
        query = session.query(
            People.email
            ).filter(
                People.username != filter_username
                )
    else:
        query = session.query(People.email)

    return query.all()


def get_people_ircnick(filter_out=None):
    """ Retrieve and return people\'s IRC nicknames."""
    query = session.query(People.ircnick)

    if filter_out:
        query = session.query(
            People.ircnick
            ).filter(
                People.username != filter_out
                )

    return query.all()


def get_people_bugzilla_email(filter_username=None):
    """ Retrieve and return registered bugzilla email. """
    if filter_username:
        query = session.query(
            People.bugzilla_email
            ).filter(
                People.username != filter_username
                )
    else:
        query = session.query(People.bugzilla_email)

    return query.all()


def get_people_by_id(id):
    """ Retrieve People by its id. """
    query = session.query(People).filter(People.id == id)
    return query.first()


def get_people_by_username(username):
    """ Retrieve People by its username.

    :param username: username to retrieve people from
    :type username: str
    :return: People's object from given username
    :rtype: fas.models.people.People
    """
    query = session.query(People).filter(People.username == username)
    return query.first()


def get_people_by_password_token(username, token):
    """ Retrieve People by its password token. """
    query = session.query(People).filter(People.username == username,
                                         People.password_token == token)

    return query.first()


def get_authenticated_user(request):
    """ Retrieve authenticated person object."""
    return get_people_by_username(unauthenticated_userid(request))


def get_people_by_email(email):
    """ Retrieve People by its email. """
    query = session.query(People).filter(People.email == email)
    return query.first()


def get_people_by_ircnick(ircnick):
    """ Retrieve by its ircnick. """
    query = session.query(People).filter(People.ircnick == ircnick)
    return query.first()


def get_account_activities_by_people_id(id):
    """ Retrieve account's activities by people's id. """
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
    """
    Retrieve account permission based on given people's token.

    :param token: Token to retrieve account permission from.
    :type token: str
    :return: Account permissions if exist otherwise, None
    :rtype: `fas.models.configs.AccountPermissions`
    """
    query = session.query(
        AccountPermissions
    ).filter(
        AccountPermissions.token == token
    )
    return query.first()


def get_certificates():
    """ Retrieve certificates."""
    query = session.query(Certificates)
    return query.all()


def get_certificate(id):
    """ Retrieve certificate from given id. """
    return session.query(Certificates).get(id)


def get_clients_certificates():
    """ Retrieve client certificates. """
    query = session.query(ClientsCertificates)
    return query.all()


def get_client_certificate(cacert, person):
    """
    Retrieve client certificate from given person
    and related group's certificate.

    :param cacert: certificate authority ID to retrieve client certificate from.
    :type cacert: `fas.models.certificates.Certificates.id`
    :param person: person to retrieve client certificate from
    :type person: `fas.models.people.People`
    :return: `fas.models.certificates.ClientsCertificates` object
    :rtype: ClientsCertificates
    """
    query = session.query(
        ClientsCertificates
        ).filter(
            ClientsCertificates.ca == cacert,
            ClientsCertificates.people == person.id
            )

    return query.first()


def get_trusted_perms():
    """
    Retrieve trusted permissions

    :return: list of trusted permissions if any, None otherwise
    :rtype: fas.models.configs.TrustedPermissions
    """
    return session.query(TrustedPermissions).all()


def get_trusted_perms_by_token(token):
    """
    Retrieve trusted permission from given token

    :param token: token id to retrieve perm from
    :type token: str
    :return: permissions found from token, None otherwise
    :rtype: fas.models.configs.TrustedPermissions
    """
    return session.query(
        TrustedPermissions).filter(
        token == TrustedPermissions.token
    ).first()