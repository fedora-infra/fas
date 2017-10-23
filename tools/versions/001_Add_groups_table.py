from sqlalchemy import Table, Column, Text, MetaData
from sqlalchemy.exc import ProgrammingError

meta = MetaData()

groups = Table(
    'groups', meta,
    Column("apply_rules", Text),    
)

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    try:
        groups.create()
    except ProgrammingError:
        print "Table exists.";

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    groups.drop()
