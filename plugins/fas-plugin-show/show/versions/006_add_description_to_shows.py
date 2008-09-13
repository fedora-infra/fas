from sqlalchemy import Table, MetaData, Text, Column
from migrate import migrate_engine
from migrate.changeset import create_column, drop_column

metadata = MetaData(migrate_engine)
shows_table = Table('show_shows', metadata, autoload=True)

description = Column('description', Text)

def upgrade():
    # Upgrade operations go here. Don't create your own engine; use the engine
    # named 'migrate_engine' imported from migrate.
    create_column(description, shows_table)

def downgrade():
    # Operations to reverse the above upgrade go here.
    drop_column(description, shows_table)
