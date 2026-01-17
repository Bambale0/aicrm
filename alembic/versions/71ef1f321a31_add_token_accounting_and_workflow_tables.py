"""add_token_accounting_and_workflow_tables

Revision ID: 71ef1f321a31
Revises: 712168a7d302
Create Date: 2026-01-17 15:41:43.384965

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "71ef1f321a31"
down_revision: Union[str, Sequence[str], None] = "712168a7d302"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create token_quotas table
    op.create_table(
        "token_quotas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=20), nullable=False, index=True),
        sa.Column("entity_id", sa.Integer(), nullable=False, index=True),
        sa.Column("quota_type", sa.String(length=50), nullable=False),
        sa.Column("limit_tokens", sa.Integer(), nullable=True),
        sa.Column("used_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reset_at", sa.DateTime(), nullable=True),
        sa.Column("alert_threshold", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    # Create token_transactions table
    op.create_table(
        "token_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quota_id", sa.Integer(), nullable=True),
        sa.Column("workflow_execution_id", sa.String(), nullable=True),
        sa.Column("ai_provider", sa.String(length=20), nullable=False),
        sa.Column("ai_model", sa.String(length=100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["quota_id"], ["token_quotas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    # Create workflows table
    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description_ai", sa.Text(), nullable=True),
        sa.Column("trigger", sa.JSON(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("actions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    # Create workflow_executions table
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("trigger_event", sa.JSON(), nullable=False),
        sa.Column(
            "execution_status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("execution_result", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    # Create action_executions table
    op.create_table(
        "action_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("execution_id", sa.Integer(), nullable=False),
        sa.Column("action_name", sa.String(length=255), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("action_config", sa.JSON(), nullable=False),
        sa.Column(
            "execution_status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("execution_result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"], ["workflow_executions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    # Create indexes for performance
    op.create_index(
        "idx_transactions_quota", "token_transactions", ["quota_id"], schema="public"
    )
    op.create_index(
        "idx_transactions_timestamp",
        "token_transactions",
        ["created_at"],
        schema="public",
    )
    op.create_index(
        "idx_quotas_entity",
        "token_quotas",
        ["entity_type", "entity_id"],
        schema="public",
    )
    op.create_index(
        "idx_executions_workflow",
        "workflow_executions",
        ["workflow_id"],
        schema="public",
    )
    op.create_index(
        "idx_action_executions_execution",
        "action_executions",
        ["execution_id"],
        schema="public",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(
        "idx_action_executions_execution",
        table_name="action_executions",
        schema="public",
    )
    op.drop_index(
        "idx_executions_workflow", table_name="workflow_executions", schema="public"
    )
    op.drop_index("idx_quotas_entity", table_name="token_quotas", schema="public")
    op.drop_index(
        "idx_transactions_timestamp", table_name="token_transactions", schema="public"
    )
    op.drop_index(
        "idx_transactions_quota", table_name="token_transactions", schema="public"
    )

    # Drop tables in reverse order
    op.drop_table("action_executions", schema="public")
    op.drop_table("workflow_executions", schema="public")
    op.drop_table("workflows", schema="public")
    op.drop_table("token_transactions", schema="public")
    op.drop_table("token_quotas", schema="public")
