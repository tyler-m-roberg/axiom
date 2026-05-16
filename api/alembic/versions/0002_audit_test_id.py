"""audit_log.test_id for permission scoping

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-15

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audit_log",
        sa.Column("test_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_audit_log_test_id", "audit_log", ["test_id"])

    # Backfill from each entity type's source-of-truth table.
    # entity_id is stored as text — cast to uuid for joins.
    op.execute(
        """
        UPDATE audit_log
        SET test_id = entity_id::uuid
        WHERE entity_type = 'test' AND test_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE audit_log AS a
        SET test_id = e.test_id
        FROM events AS e
        WHERE a.entity_type = 'event'
          AND a.test_id IS NULL
          AND a.entity_id = e.id::text
        """
    )
    op.execute(
        """
        UPDATE audit_log AS a
        SET test_id = b.test_id
        FROM test_field_bindings AS b
        WHERE a.entity_type = 'test_field_binding'
          AND a.test_id IS NULL
          AND a.entity_id = b.id::text
        """
    )
    op.execute(
        """
        UPDATE audit_log AS a
        SET test_id = acl.test_id
        FROM test_acls AS acl
        WHERE a.entity_type = 'test_acl'
          AND a.test_id IS NULL
          AND a.entity_id = acl.id::text
        """
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_test_id", table_name="audit_log")
    op.drop_column("audit_log", "test_id")
