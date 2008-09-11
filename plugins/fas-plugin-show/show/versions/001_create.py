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
