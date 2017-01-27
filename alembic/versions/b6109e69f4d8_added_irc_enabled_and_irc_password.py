"""Added 'irc_enabled' and 'irc_password' fields to People

Revision ID: b6109e69f4d8
Revises: c3f6e45190ca
Create Date: 2017-01-27 17:54:27.841432

"""

# revision identifiers, used by Alembic.
revision = 'b6109e69f4d8'
down_revision = 'c3f6e45190ca'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('people', sa.Column('irc_enabled', sa.Boolean(), default=False))
    op.add_column('people', sa.Column('irc_password', sa.UnicodeText(), nullable=True))


def downgrade():
    op.drop_column('people', 'irc_password')
    op.drop_column('people', 'irc_enabled')
