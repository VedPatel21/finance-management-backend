"""Updated migration

Revision ID: 49e7a8c1a40d
Revises: e33f38ef28ec
Create Date: 2025-03-22 14:47:20.523158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49e7a8c1a40d'
down_revision = 'e33f38ef28ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fee_transaction_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('student_name', sa.String(length=100), nullable=False),
    sa.Column('class_name', sa.String(length=50), nullable=False),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('mode', sa.String(length=20), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('fee_remaining', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('fee_transaction_history')
    # ### end Alembic commands ###
