from sqlalchemy import Table, Column, MetaData, Text, UnicodeText

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    groups = Table('groups', meta, autoload=True)
    groups.c.apply_rules.alter(type=UnicodeText)

def downgrade():
    meta = MetaData(bind=migrate_engine)
    groups = Table('groups', meta, autoload=True)
    groups.c.apply_rules.alter(type=Text)
