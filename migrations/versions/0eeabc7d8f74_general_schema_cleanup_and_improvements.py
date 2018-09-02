"""General schema cleanup and improvements

Revision ID: 0eeabc7d8f74
Revises: b1c013f236ab
Create Date: 2018-08-31 18:07:19.767140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0eeabc7d8f74'
down_revision = 'b1c013f236ab'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('signature_fresh', 'freshman', new_column_name='freshman_username')


def downgrade():
    op.alter_column('signature_fresh', 'freshman_username', new_column_name='freshman')
