# -*- coding: utf-8 -*-

import sqlalchemy as sa

from fas.models import AccountStatus, RoleLevel
from fas.models.group import Groups, GroupType
from fas.models.people import People
from fas.models.la import LicenseAgreement, SignedLicenseAgreement
from fas.models.configs import AccountPermissions


## Method to get AccountStatus

def get_accountstatus(session):
    """ Retrieve all the status an account can have. """
    query = session.query(People).filter(People.status)
    return query.all()


def get_accountstatus_by_status(session, status):
    """ Retrieve the status an account can have for the specified status.
    """
    query = session.query(
        AccountStatus
    ).filter(
        sa.func.lower(AccountStatus.status) == sa.func.lower(status)
    )
    return query.first()


## Method to get RoleLevel

def get_role_levels(session):
    """ Retrieve all the roles someone can have in a group. """
    query = session.query(RoleLevel)
    return query.all()


## Method to interact with Groups

def get_groups(session, limit=None, offset=None):
    """ Retrieve all registered groups from databse. """
    query = session.query(Groups)

    if limit and offset:
        query.slice(offset, limit)

    return query.all()


def get_group_by_id(session, id):
    """ Retrieve Groups by its id. """
    query = session.query(Groups).filter(Groups.id == id)
    return query.first()


def get_group_by_name(session, name):
    """ Retrieve Groups by its name. """
    query = session.query(Groups).filter(Groups.name == name)
    return query.first()


## Method to interact with GroupType

def get_grouptype_by_id(session, id):
    """ Retrive GroupType by its id. """
    query = session.query(GroupType).filter(GroupType.id == id)
    return query.first()


## Method to interact with People

def get_people(session, limit=None, offset=None):
    """ Retrieve all registered people from database. """
    query = session.query(People)

    if limit and offset:
        query.slice(offset, limit)

    return query.all()


def get_people_by_id(session, id):
    """ Retrieve People by its id. """
    query = session.query(People).filter(People.id == id)
    return query.first()


def get_people_by_username(session, username):
    """ Retrieve People by its username. """
    query = session.query(People).filter(People.username == username)
    return query.first()


def get_people_by_email(session, email):
    """ Retrieve People by its email. """
    query = session.query(People).filter(People.email == email)
    return query.first()


def get_people_by_ircnick(session, ircnick):
    """ Retrieve by its ircnick. """
    query = session.query(People).filter(People.ircnick == ircnick)
    return query.first()


def get_licenses(session):
    """ Retrieve all licenses from database. """
    query = session.query(LicenseAgreement)
    return query.all()


def get_license_by_id(session, id):
    """ Retrieve license based on given id"""
    query = session.query(LicenseAgreement).filter(
                                            LicenseAgreement.id == id)
    return query.first()


def get_account_permissions_by_people_id(session, id):
    """ Retrieve account permissions based on given people's id. """
    query = session.query(AccountPermissions).filter(
                                            AccountPermissions.people == id
                                            )
    return query.all()