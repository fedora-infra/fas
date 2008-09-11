from sqlalchemy import *
from migrate import *

shows_table = Table('show_shows', metadata,
                    Column('id', Integer,
                           autoincrement=True,
                           primary_key=True),
                    Column('name', Text),
                    Column('owner', Text),
                    Column('group_id', Integer,
                           ForeignKey('groups.id')),
                    Column('long_name', Text))


def upgrade():
    # Upgrade operations go here. Don't create your own engine; use the engine
    # named 'migrate_engine' imported from migrate.
    shows_table.create()
    pass

def downgrade():
    # Operations to reverse the above upgrade go here.
    shows_table.drop()
    pass
