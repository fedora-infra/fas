from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from migrate import migrate_engine

metadata = MetaData(migrate_engine)

shows_table = Table('show_shows', metadata, autoload=True)
PeopleTable = Table('people', metadata, autoload=True)

user_signups_table = \
    Table('show_user_signups', metadata,
          Column('id', Integer,
                 autoincrement=True,
                 primary_key=True),
          Column('show_id', Integer,
                 ForeignKey('show_shows.id')),
          Column('people_id', Integer,
                 ForeignKey('people.id'),
                 unique=True))

def upgrade():
    # Upgrade operations go here. Don't create your own engine; use the engine
    # named 'migrate_engine' imported from migrate.
    user_signups_table.create()

def downgrade():
    # Operations to reverse the above upgrade go here.
    user_signups_table.drop()
