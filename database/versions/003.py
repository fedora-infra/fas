# 
from sqlalchemy import Table, Column, MetaData, Text, UnicodeText
from migrate import migrate_engine
from migrate.changeset import alter_column

metadata = MetaData(migrate_engine)

GroupsTable = Table('groups', metadata, autoload=True)
col = GroupsTable.c.apply_rules

def upgrade():
	alter_column(col, type=UnicodeText)

def downgrade():
	alter_column(col, type=Text) 
