"""created courses table.

Revision ID: 8d2ae9bf24fd
Revises: eebca538cad5
Create Date: 2024-03-27 17:03:34.229856

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8d2ae9bf24fd"
down_revision: str | None = "eebca538cad5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade version."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_courses_id"), "courses", ["id"], unique=False)
    op.create_index(op.f("ix_courses_name"), "courses", ["name"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade version."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_courses_name"), table_name="courses")
    op.drop_index(op.f("ix_courses_id"), table_name="courses")
    op.drop_table("courses")
    # ### end Alembic commands ###
