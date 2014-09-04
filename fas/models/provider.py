# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy import func

from fas.models import DBSession as session
from fas.models import AccountStatus, RoleLevel
from fas.models.group import Groups, GroupType, GroupMembership
from fas.models.people import People
from fas.models.people import PeopleAccountActivitiesLog
from fas.models.la import LicenseAgreement, SignedLicenseAgreement
from fas.models.configs import AccountPermissions


def __get_listoffset(page, limit):
    """ Get offset based on requeted limit. """
    offset = (page - 1) * limit

    if offset < limit:
        offset = -1
    else:
        offset += 1

    return offset


## Method to get AccountStatus


def get_accountstatus():
    """ Retrieve all the status an account can have. """
    query = session.query(AccountStatus)
    return query.all()


def get_accountstatus_by_status(status):
    """ Retrieve the status an account can have for the specified status.
    """
    query = session.query(
        AccountStatus
    ).filter(
        sa.func.lower(AccountStatus.status) == sa.func.lower(status)
    )
    return query.first()


## Method to get RoleLevel

def get_role_levels():
    """ Retrieve all the roles someone can have in a group. """
    query = session.query(RoleLevel)
    return query.all()


## Method to interact with Groups

def get_groups_count():
    """ Return people count. """
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
    query = session.query(Groups.name).filter(Groups.parent_group_id == -1) \
            .order_by(Groups.name)
    return query.all()

def get_child_groups():
    """ Retrieve all child groups."""
    query = session.query(Groups).filter(Groups.parent_group_id >= -1)

def get_group_by_id(id):
    """ Retrieve Groups by its id. """
    query = session.query(Groups).filter(Groups.id == id)
    return query.first()


def get_group_by_name(name):
    """ Retrieve Groups by its name. """
    query = session.query(Groups).filter(Groups.name == name)
    return query.first()


def get_group_membership(id):
    """ Retrieve group's membership by group's id"""
    query = session.query(Groups, GroupMembership, People, RoleLevel)\
    .join((GroupMembership, GroupMembership.group_id == Groups.id))\
    .join(People, People.id == GroupMembership.people_id)\
    .join(RoleLevel)\
    .filter(Groups.id == id,)

    return query.all()

def get_group_by_people_membership(username):
    """ Retrieve group's membership by people's username."""
    query = session.query(Groups)\
    .join((GroupMembership, GroupMembership.group_id == Groups.id))\
    .join(People, People.username == username)

    return query.all()

def get_group_types():
    """ Retrieve group's types."""
    query = session.query(GroupType)
    return query.all()

## Method to interact with GroupType

def get_grouptype_by_id(id):
    """ Retrive GroupType by its id. """
    query = session.query(GroupType).filter(GroupType.id == id)
    return query.first()


## Method to interact with People

def get_people_count():
    """ Return people count. """
    return session.query(func.count(People.id)).first()[0]


def get_people(limit=None, page=None):
    """ Retrieve all registered people from database. """
    if limit and page:
        query = session.query(People) \
        .order_by(People.username)\
        .limit(limit) \
        .offset(__get_listoffset(page, limit))
    else:
        query = session.query(People).order_by(People.username)

    return query.all()

def get_people_username():
    """ Retrieve and return list of tuple of people's username and id."""
    query = session.query(People.id, People.username).order_by(People.username)
    return query.all()

def get_people_by_id(id):
    """ Retrieve People by its id. """
    query = session.query(People).filter(People.id == id)
    return query.first()


def get_people_by_username(username):
    """ Retrieve People by its username. """
    query = session.query(People).filter(People.username == username)
    return query.first()


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
    query = session.query(PeopleAccountActivitiesLog)\
    .filter(PeopleAccountActivitiesLog.people == id)

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
