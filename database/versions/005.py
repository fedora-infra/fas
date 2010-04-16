# 
from sqlalchemy import Table, Column, MetaData, Boolean
from migrate import migrate_engine
from migrate.changeset import create_column, drop_column

metadata = MetaData(migrate_engine)

GroupsTable = Table('groups', metadata, autoload=True)
col = Column('invite_only', Boolean, default=False)

def upgrade():
    create_column(col, GroupsTable)

def downgrade():
    drop_column(col, GroupsTable)

