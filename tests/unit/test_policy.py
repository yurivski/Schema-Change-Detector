"""
Testes de carregamento e aplicação de política.
Pra evitar que o arquivo fique muito grande, apenas as chamadas com argumentos
acima de 100 caracteres terão quebras de linhas.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from driftbrake.exceptions import PolicyError
from driftbrake.models import ChangeType, DiffResult, SchemaChange, Severity
from driftbrake.policy import Policy, apply_policy, load_policy

# helpers


def _change(
    severity: Severity,
    table: str = "users",
    column: str = "email",
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        severity=severity,
        schema_name="public",
        table_name=table,
        column_name=column,
        field_name=None,
        old_value="text",
        new_value=None,
        description="test change",
    )


def _write_yaml(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# load_policy


def test_load_policy_none_returns_empty():
    policy = load_policy(None)
    assert isinstance(policy, Policy)
    assert policy.overrides == {}
    assert policy.ignore_tables == []
    assert policy.ignore_columns == []


def test_load_policy_valid_yaml():
    path = _write_yaml("""
overrides:
  column_removed: WARNING
  table_added: SAFE

ignore_tables:
  - audit_log
  - tmp_staging

ignore_columns:
  - users.updated_at
""")
    try:
        policy = load_policy(path)
        assert policy.overrides["column_removed"] == "WARNING"
        assert policy.overrides["table_added"] == "SAFE"
        assert "audit_log" in policy.ignore_tables
        assert "tmp_staging" in policy.ignore_tables
        assert "users.updated_at" in policy.ignore_columns
    finally:
        os.unlink(path)


def test_load_policy_empty_yaml_returns_empty():
    path = _write_yaml("")
    try:
        policy = load_policy(path)
        assert policy.overrides == {}
    finally:
        os.unlink(path)


def test_load_policy_missing_file_raises():
    with pytest.raises(PolicyError, match="not found"):
        load_policy("/tmp/this_file_does_not_exist_driftbrake.yml")


def test_load_policy_malformed_yaml_raises():
    path = _write_yaml("overrides: [invalid: yaml: structure")
    try:
        with pytest.raises(PolicyError):
            load_policy(path)
    finally:
        os.unlink(path)


def test_load_policy_invalid_severity_raises():
    path = _write_yaml("overrides:\n  column_removed: TYPO\n")
    try:
        with pytest.raises(PolicyError, match="Invalid severity"):
            load_policy(path)
    finally:
        os.unlink(path)


def test_load_policy_severity_case_insensitive():
    path = _write_yaml("overrides:\n  column_removed: breaking\n")
    try:
        policy = load_policy(path)
        assert policy.overrides["column_removed"] == "BREAKING"
    finally:
        os.unlink(path)


# apply_policy


def test_apply_policy_no_overrides_returns_unchanged():
    result = DiffResult(changes=[_change(Severity.BREAKING)])
    policy = Policy()
    out = apply_policy(result, policy)
    assert out is result  # sem modificações, retorna o mesmo objeto


def test_apply_policy_ignores_table():
    result = DiffResult(
        changes=[
            _change(Severity.BREAKING, table="audit_log"),
            _change(Severity.SAFE, table="users"),
        ]
    )
    policy = Policy(ignore_tables=["audit_log"])
    out = apply_policy(result, policy)
    assert len(out.changes) == 1
    assert out.changes[0].table_name == "users"


def test_apply_policy_ignores_column():
    result = DiffResult(
        changes=[
            _change(Severity.BREAKING, table="users", column="updated_at"),
            _change(Severity.SAFE, table="users", column="email"),
        ]
    )
    policy = Policy(ignore_columns=["users.updated_at"])
    out = apply_policy(result, policy)
    assert len(out.changes) == 1
    assert out.changes[0].column_name == "email"


def test_apply_policy_overrides_severity():
    result = DiffResult(changes=[_change(Severity.BREAKING, change_type=ChangeType.COLUMN_REMOVED)])
    policy = Policy(overrides={"column_removed": "WARNING"})
    out = apply_policy(result, policy)
    assert out.changes[0].severity == Severity.WARNING


def test_apply_policy_preserves_metadata():
    from datetime import datetime

    ts = datetime(2026, 1, 1)
    result = DiffResult(
        changes=[_change(Severity.SAFE)],
        compared_at=ts,
        expected_source="a",
        current_source="b",
    )
    policy = Policy(ignore_tables=["non_existent"])
    out = apply_policy(result, policy)
    assert out.compared_at == ts
    assert out.expected_source == "a"
    assert out.current_source == "b"
