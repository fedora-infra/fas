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

from sqlalchemy import *
from migrate import *
from migrate.changeset import *

metadata = MetaData(migrate_engine)

shows_table = Table('show_shows', metadata,
                    Column('id', Integer,
                           autoincrement=True,
                           primary_key=True),
                    Column('name', Text),
                    Column('owner', Text),
                    Column('group_id', Integer),
                    Column('long_name', Text))

GroupsTable = Table('groups', metadata, autoload=True)

shows_group_fk = ForeignKeyConstraint([shows_table.c.group_id], 
                                      [GroupsTable.c.id])


def upgrade():
    # Upgrade operations go here. Don't create your own engine; use the engine
    # named 'migrate_engine' imported from migrate.
    shows_table.create()
    shows_group_fk.create()

def downgrade():
    # Operations to reverse the above upgrade go here.
    shows_group_fk.drop()
    shows_table.drop()
