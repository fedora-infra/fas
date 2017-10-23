from sqlalchemy import Table, Boolean, Column, MetaData
from sqlalchemy.exc import ProgrammingError

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    people = Table('people', meta, autoload=True)
    privacyc = Column("privacy", Boolean, default=False, nullable=False)
    try:
        privacyc.create(people)
    except ProgrammingError:
        print "Column exists."

def downgrade():
    meta = MetaData(bind=migrate_engine)
    people = Table('people', meta, autoload=True)
    people.c.privacy.drop()
