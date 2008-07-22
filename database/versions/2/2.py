# 
from sqlalchemy import Table, Column, MetaData, Boolean, PassiveDefault, text
from migrate import migrate_engine
from migrate.changeset import create_column, drop_column

metadata = MetaData(migrate_engine)

PeopleTable = Table('people', metadata, autoload=True)
col = Column('privacy', Boolean, PassiveDefault(text('False')), nullable=False)

def upgrade():
    create_column(col, PeopleTable)

def downgrade():
    drop_column(col, PeopleTable)

