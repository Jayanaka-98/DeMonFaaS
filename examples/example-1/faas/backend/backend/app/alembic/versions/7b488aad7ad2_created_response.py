"""created response.

Revision ID: 7b488aad7ad2
Revises: 060e7bd0b679
Create Date: 2024-04-03 12:29:22.244184

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b488aad7ad2"
down_revision: str | None = "060e7bd0b679"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade version."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=True),
        sa.Column("is_private", sa.Boolean(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=True),
        sa.Column("body", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade version."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("responses")
    # ### end Alembic commands ###
