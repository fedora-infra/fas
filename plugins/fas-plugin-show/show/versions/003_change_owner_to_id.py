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
