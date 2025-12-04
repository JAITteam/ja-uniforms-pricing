"""Add unique constraints to junction tables

Revision ID: 9daa4459fcc3
Revises: 9d88d1fe32a3
Create Date: 2025-12-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9daa4459fcc3'
down_revision = '9d88d1fe32a3'
branch_labels = None
depends_on = None


def upgrade():
    # Add unique constraints to junction tables
    # Using batch mode for SQLite compatibility, works on PostgreSQL too
    
    # StyleFabric - add unique constraint
    with op.batch_alter_table('style_fabrics', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_style_fabric', ['style_id', 'fabric_id'])

    # StyleNotion - add unique constraint
    with op.batch_alter_table('style_notions', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_style_notion', ['style_id', 'notion_id'])

    # StyleColor - add unique constraint
    with op.batch_alter_table('style_colors', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_style_color', ['style_id', 'color_id'])

    # StyleVariable - add unique constraint
    with op.batch_alter_table('style_variables', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_style_variable', ['style_id', 'variable_id'])

    # StyleLabor - add unique constraint
    with op.batch_alter_table('style_labor', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_style_labor', ['style_id', 'labor_operation_id'])


def downgrade():
    # Remove constraints (reverse of upgrade)
    with op.batch_alter_table('style_labor', schema=None) as batch_op:
        batch_op.drop_constraint('uq_style_labor', type_='unique')

    with op.batch_alter_table('style_variables', schema=None) as batch_op:
        batch_op.drop_constraint('uq_style_variable', type_='unique')

    with op.batch_alter_table('style_colors', schema=None) as batch_op:
        batch_op.drop_constraint('uq_style_color', type_='unique')

    with op.batch_alter_table('style_notions', schema=None) as batch_op:
        batch_op.drop_constraint('uq_style_notion', type_='unique')

    with op.batch_alter_table('style_fabrics', schema=None) as batch_op:
        batch_op.drop_constraint('uq_style_fabric', type_='unique')