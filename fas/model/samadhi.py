# -*- coding: utf-8 -*-

# Copyright 2008 by Jeffrey C. Ollie
#
# This file is part of Samadhi.
#
# Samadhi is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License.
#
# Samadhi is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Samadhi.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
from turbogears.database import metadata, mapper, session
# import some basic SQLAlchemy classes for declaring the data model
# (see http://www.sqlalchemy.org/docs/04/ormtutorial.html)
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import relation
# import some datatypes for table columns from SQLAlchemy
# (see http://www.sqlalchemy.org/docs/04/types.html for more)
from sqlalchemy import String, Unicode, Integer, DateTime, PrimaryKeyConstraint
from turbogears import identity

from sqlalchemy.types import TypeEngine

from openid.association import Association as OpenIDAssociation
from openid.store.interface import OpenIDStore

# create our own custom type to keep from running afoul of
# SQLAlchemy's automatic UTF-8 encoding/decoding.
class HexString(TypeEngine):
    def __init__(self, length):
        self.length = length

    def get_col_spec(self):
        return 'VARCHAR(%i)' % (self.length * 2)

    def convert_bind_param(self, value, engine):
        return value.encode('hex')

    def convert_result_value(self, value, engine):
        return value.decode('hex')

samadhi_associations_table = Table('samadhi_associations', metadata,
                                   Column('server_url',String(2048), nullable = False),
                                   Column('handle', String(128), nullable = False),
                                   Column('secret', HexString(128), nullable = False),
                                   Column('issued', Integer, nullable = False),
                                   Column('lifetime', Integer, nullable = False),
                                   Column('assoc_type', String(64), nullable = False),
                                   PrimaryKeyConstraint('server_url', 'handle'))

class SamadhiAssociation(object):
    @classmethod
    def get(cls, server_url, handle = None):
        if handle is None:
            return cls.query.filter_by(server_url = server_url).order_by(issued.desc()).first()
        else:
            return cls.query.filter_by(server_url = server_url, handle = handle).order_by(issued.desc()).first()

    @classmethod
    def remove(cls, server_url, handle):
        for a in cls.query.filter_by(server_url = server_url, handle = handle):
            session.delete(a)

mapper(SamadhiAssociation, samadhi_associations_table)

samadhi_nonces_table = Table('samadhi_nonces', metadata,
                             Column('server_url', HexString(2048), nullable = False),
                             Column('timestamp', Integer, nullable = False),
                             Column('salt', HexString(40), nullable = False),
                             PrimaryKeyConstraint('server_url', 'timestamp', 'salt'))

class SamadhiNonce(object):
    pass

mapper(SamadhiNonce, samadhi_nonces_table)

# Implement an OpenID "store", which is how the OpenID library stores
# persisent data.  Here's the docs that describe it:
#
# http://openidenabled.com/files/python-openid/docs/2.1.1/openid.store.interface.OpenIDStore-class.html

class SamadhiStore(OpenIDStore):
    def storeAssociation(self, server_url, association):
        a = SamadhiAssociation(server_url = server_url,
                               handle = association.handle,
                               secret = association.secret,
                               issued = association.issued,
                               lifetime = association.lifetime,
                               assoc_type = association.assoc_type)

    def getAssociation(self, server_url, handle=None):
        a = SamadhiAssociation.get(server_url, handle)
        if a:
            return OpenIDAssociation(a.handle,
                                     a.secret,
                                     a.issued,
                                     a.lifetime,
                                     a.assoc_type)
        return None

    def removeAssociation(self, server_url, handle):
        SamadhiAssociation.remove(server_url, handle)

    def useNonce(self, server_url, timestamp, salt):
        n = SamadhiNonce(server_url = server_url,
                         timestamp = timestamp,
                         salt = salt)

    def cleanupNonces(self):
        return 0

    def cleanupAssociations(self):
        return 0

