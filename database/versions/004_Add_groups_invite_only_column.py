from sqlalchemy import Table, Column, MetaData, Boolean
from sqlalchemy.exc import ProgrammingError

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    groups = Table('groups', meta, autoload=True)
    invite_onlyc = Column('invite_only', Boolean, default=False)
    try:
        invite_onlyc.create(groups)
    except ProgrammingError:
        print "Column exists."

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    groups = Table('groups', meta, autoload=True)
    groups.c.invite_only.drop()
