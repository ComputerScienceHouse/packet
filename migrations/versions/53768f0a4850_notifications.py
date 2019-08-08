"""notifications

Revision ID: 53768f0a4850
Revises: eecf30892d0e
Create Date: 2019-08-06 22:15:04.400982

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53768f0a4850'
down_revision = 'eecf30892d0e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notification_subscriptions',
    sa.Column('member', sa.String(length=36), nullable=True),
    sa.Column('freshman_username', sa.String(length=10), nullable=True),
    sa.Column('token', sa.String(length=256), nullable=False),
    sa.ForeignKeyConstraint(['freshman_username'], ['freshman.rit_username'], ),
    sa.PrimaryKeyConstraint('token')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('notification_subscriptions')
    # ### end Alembic commands ###
