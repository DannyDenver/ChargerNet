"""empty message

Revision ID: a944193aec64
Revises: ddff0fac4b35
Create Date: 2022-02-12 16:17:29.664656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a944193aec64'
down_revision = 'ddff0fac4b35'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Car', sa.Column('plug_type', sa.String(length=20), nullable=True))
    op.drop_column('Car', 'charger_type')
    op.add_column('Charger', sa.Column('plug_type', sa.String(length=20), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Charger', 'plug_type')
    op.add_column('Car', sa.Column('charger_type', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.drop_column('Car', 'plug_type')
    # ### end Alembic commands ###