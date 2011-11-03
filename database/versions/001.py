# 
from sqlalchemy import Table, Column, Text, MetaData

metadata = MetaData()

groups = Table(
    'groups', metadata,
    Column("apply_rules", Text),    
)

def upgrade():
    meta.bind = migrate_engine
    groups.create()	

def downgrade():
    meta.bind = migrate_engine
    groups.drop()
