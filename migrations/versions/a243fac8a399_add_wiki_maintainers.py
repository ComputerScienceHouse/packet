"""Add Wiki Maintainers

Revision ID: a243fac8a399
Revises: 53768f0a4850
Create Date: 2020-09-02 15:20:48.285910

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a243fac8a399'
down_revision = '53768f0a4850'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('signature_upper', sa.Column('w_m', sa.Boolean(), nullable=False, server_default='f'))


def downgrade():
    op.drop_column('signature_upper', 'w_m')
