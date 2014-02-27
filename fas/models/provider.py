# -*- coding: utf-8 -*-

from fas.models.group import Groups
from fas.models.people import People


## Method to interact with Groups

def get_group_by_id(session, id):
    """ Retrieve a specific Groups by its id. """
    query = session.query(Groups).filter(Groups.id == id)
    return query.first()


def get_group_by_name(session, name):
    """ Retrieve a specific Groups by its name. """
    query = session.query(Groups).filter(Groups.name == name)
    return query.first()


## Method to interact with GroupType

def get_grouptype_by_id(session, id):
    """ Retrive a specific GroupType by its id. """
    query = session.query(GroupType).filter(GroupType.id == id)
    return query.first()


## Method to interact with People

def get_people_by_id(session, id):
    """ Retrieve a specific People by its id. """
    query = session.query(People).filter(People.id == id)
    return query.first()


def get_people_by_username(session, username):
    """ Retrieve a specific People by its username. """
    query = session.query(People).filter(People.username == username)
    return query.first()


def get_people_by_email(session, email):
    """ Retrieve a specific People by its email. """
    query = session.query(People).filter(People.email == email)
    return query.first()


def get_people_by_ircnick(session, ircnick):
    """ Retrieve a specific People by its ircnick. """
    query = session.query(People).filter(People.ircnick == ircnick)
    return query.first()
