"""Add aws url

Revision ID: 86d907504dfe
Revises: 3f547318cab0
Create Date: 2024-12-17 13:18:20.093033

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "86d907504dfe"
down_revision: Union[str, None] = "3f547318cab0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("id_documents", sa.Column("verified", sa.Boolean(), nullable=False))
    op.add_column("id_documents", sa.Column("urls", sa.JSON(), nullable=False))
    op.drop_column("id_documents", "url")
    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    op.create_unique_constraint(op.f("uq_users_phone"), "users", ["phone"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f("uq_users_phone"), "users", type_="unique")
    op.drop_column("users", "phone")
    op.add_column(
        "id_documents",
        sa.Column("url", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    )
    op.drop_column("id_documents", "urls")
    op.drop_column("id_documents", "verified")
    # ### end Alembic commands ###
