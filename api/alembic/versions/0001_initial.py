"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-14

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    field_data_type = postgresql.ENUM(
        "string", "number", "bool", "date", "enum", name="field_data_type", create_type=True
    )
    field_scope = postgresql.ENUM("test", "event", "both", name="field_scope", create_type=True)
    field_status = postgresql.ENUM(
        "established", "on_the_fly", name="field_status", create_type=True
    )

    op.create_table(
        "metadata_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("data_type", field_data_type, nullable=False),
        sa.Column("enum_values", postgresql.JSONB(), nullable=True),
        sa.Column("scope", field_scope, nullable=False),
        sa.Column("status", field_status, nullable=False),
        sa.Column("namespace_group_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("namespace_group_id", "key", name="uq_metadata_fields_namespace_key"),
    )
    op.create_index("ix_metadata_fields_key", "metadata_fields", ["key"])
    op.create_index(
        "ix_metadata_fields_namespace_group_id", "metadata_fields", ["namespace_group_id"]
    )

    binding_requirement = postgresql.ENUM(
        "required", "optional", name="binding_requirement", create_type=True
    )
    binding_applies = postgresql.ENUM("test", "event", name="binding_applies", create_type=True)

    op.create_table(
        "test_field_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "test_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("metadata_fields.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("requirement", binding_requirement, nullable=False),
        sa.Column("applies_to", binding_applies, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("test_id", "field_id", "applies_to", name="uq_binding_test_field_scope"),
    )
    op.create_index("ix_test_field_bindings_test_id", "test_field_bindings", ["test_id"])
    op.create_index("ix_test_field_bindings_field_id", "test_field_bindings", ["field_id"])

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "test_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("on_the_fly_field_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_events_test_id", "events", ["test_id"])

    acl_permission = postgresql.ENUM(
        "read", "write", "admin", name="acl_permission", create_type=True
    )

    op.create_table(
        "test_acls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "test_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("group_id", sa.String(length=64), nullable=False),
        sa.Column("permission", acl_permission, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("test_id", "group_id", name="uq_test_acl_test_group"),
    )
    op.create_index("ix_test_acls_test_id", "test_acls", ["test_id"])
    op.create_index("ix_test_acls_group_id", "test_acls", ["group_id"])

    audit_action = postgresql.ENUM(
        "create", "update", "delete", "promote", name="audit_action", create_type=True
    )

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("actor_sub", sa.String(length=128), nullable=True),
        sa.Column("actor_username", sa.String(length=255), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("before", postgresql.JSONB(), nullable=True),
        sa.Column("after", postgresql.JSONB(), nullable=True),
        sa.Column("diff", postgresql.JSONB(), nullable=True),
        sa.Column("context", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_audit_log_entity_type", "audit_log", ["entity_type"])
    op.create_index("ix_audit_log_entity_id", "audit_log", ["entity_id"])
    op.create_index("ix_audit_log_at", "audit_log", ["at"])

    op.create_table(
        "sessions",
        sa.Column("sid", sa.String(length=128), primary_key=True),
        sa.Column("user_sub", sa.String(length=128), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("claims", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("id_token_enc", sa.LargeBinary(), nullable=True),
        sa.Column("access_token_enc", sa.LargeBinary(), nullable=True),
        sa.Column("refresh_token_enc", sa.LargeBinary(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sessions_user_sub", "sessions", ["user_sub"])


def downgrade() -> None:
    op.drop_index("ix_sessions_user_sub", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_audit_log_at", table_name="audit_log")
    op.drop_index("ix_audit_log_entity_id", table_name="audit_log")
    op.drop_index("ix_audit_log_entity_type", table_name="audit_log")
    op.drop_table("audit_log")
    op.execute("DROP TYPE IF EXISTS audit_action")
    op.drop_index("ix_test_acls_group_id", table_name="test_acls")
    op.drop_index("ix_test_acls_test_id", table_name="test_acls")
    op.drop_table("test_acls")
    op.execute("DROP TYPE IF EXISTS acl_permission")
    op.drop_index("ix_events_test_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_test_field_bindings_field_id", table_name="test_field_bindings")
    op.drop_index("ix_test_field_bindings_test_id", table_name="test_field_bindings")
    op.drop_table("test_field_bindings")
    op.execute("DROP TYPE IF EXISTS binding_applies")
    op.execute("DROP TYPE IF EXISTS binding_requirement")
    op.drop_index("ix_metadata_fields_namespace_group_id", table_name="metadata_fields")
    op.drop_index("ix_metadata_fields_key", table_name="metadata_fields")
    op.drop_table("metadata_fields")
    op.execute("DROP TYPE IF EXISTS field_status")
    op.execute("DROP TYPE IF EXISTS field_scope")
    op.execute("DROP TYPE IF EXISTS field_data_type")
    op.drop_table("tests")
