# -*- coding: utf-8 -*-
#
# Copyright © 2008 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Yaakov Nemoy <ynemoy@redhat.com>
#

from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from migrate import migrate_engine

metadata = MetaData(migrate_engine)

shows_table = Table('show_shows', metadata, autoload=True)
PeopleTable = Table('people', metadata, autoload=True)

user_signups_table = \
    Table('show_user_signups', metadata,
          Column('id', Integer,
                 autoincrement=True,
                 primary_key=True),
          Column('show_id', Integer,
                 ForeignKey('show_shows.id')),
          Column('people_id', Integer,
                 ForeignKey('people.id'),
                 unique=True))

def upgrade():
    # Upgrade operations go here. Don't create your own engine; use the engine
    # named 'migrate_engine' imported from migrate.
    user_signups_table.create()

def downgrade():
    # Operations to reverse the above upgrade go here.
    user_signups_table.drop()
