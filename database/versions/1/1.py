# 
from sqlalchemy import Table, Column, MetaData, Text
from migrate import migrate_engine
from migrate.changeset import create_column, drop_column

metadata = MetaData(migrate_engine)

GroupsTable = Table('groups', metadata, autoload=True)
col = Column("apply_rules", Text)

def upgrade():
	create_column(col, GroupsTable)

def downgrade():
	drop_column(col, GroupsTable)

