"""Dhruva.AI V2 — PostgreSQL Row-Level Security (RLS) Generator & Verifier.

Provides RLS DDL statement generation for Alembic migrations and tenant isolation verification.
"""

from typing import List


TENANT_ISOLATED_TABLES: List[str] = [
    "users",
    "roles",
    "user_roles",
    "refresh_tokens",
    "audit_logs",
]


def generate_enable_rls_sql(table_name: str) -> str:
    """Generate SQL statement to enable Row-Level Security on a table."""
    return f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"


def generate_tenant_policy_sql(table_name: str) -> str:
    """Generate SQL policy enforcing tenant isolation via `app.current_institution_id`."""
    return f"""
    CREATE POLICY tenant_isolation_policy ON {table_name}
    FOR ALL
    USING (
        institution_id IS NULL OR
        institution_id = NULLIF(current_setting('app.current_institution_id', true), '')::uuid
    );
    """.strip()


def generate_drop_tenant_policy_sql(table_name: str) -> str:
    """Generate SQL to drop tenant isolation policy."""
    return f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table_name};"
