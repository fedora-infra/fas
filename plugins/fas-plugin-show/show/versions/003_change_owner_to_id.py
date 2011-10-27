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
from migrate.changeset.schema import *
import pdb

metadata = MetaData(migrate_engine)

owner = Column('owner', Text)
owner_id = Column('owner_id', Integer)

shows_table = Table('show_shows', metadata, autoload=True)

PeopleTable = Table('people', metadata, autoload=True)

def upgrade():
    # Upgrade operations go here. Don't create your own engine; use the engine
    # named 'migrate_engine' imported from migrate.
    create_column(owner_id, shows_table)

    owners = select([shows_table.c.id, shows_table.c.owner, 
                     PeopleTable.c.id],
                     shows_table.c.owner==PeopleTable.c.username).execute()
    for x in owners:
        shows_table.update(shows_table.c.id==x[0], values=dict(owner_id=x[2])).execute()
    
    drop_column(owner, shows_table)
    pass

def downgrade():
    # Operations to reverse the above upgrade go here.
    create_column(owner, shows_table)
    
    owners = select([shows_table.c.id, shows_table.c.owner_id, 
                     PeopleTable.c.username],
                     shows_table.c.owner_id==PeopleTable.c.id).execute()
    for x in owners:
        shows_table.update(shows_table.c.id==x[0], values=dict(owner=x[2])).execute()

    drop_column(owner_id, shows_table)
    pass
