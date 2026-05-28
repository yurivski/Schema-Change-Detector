# Policy - overrides de severidade e listas de ignore por projeto.

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from driftbrake.exceptions import PolicyError


@dataclass
class Policy:
    overrides: dict[str, str] = field(default_factory=dict)
    """Mapeia nome-da-mudança -> severidade (BREAKING|WARNING|SAFE)."""

    ignore_tables: list[str] = field(default_factory=list)
    """Tabelas a ignorar totalmente no scan."""

    ignore_columns: list[str] = field(default_factory=list)
    """Colunas a ignorar. Formato: 'tabela.coluna'."""


def load_policy(path: str | None) -> Policy:
    """Carrega YAML. Se path=None, retorna Policy() vazia."""
    if path is None:
        return Policy()

    try:
        import yaml
    except ImportError as exc:
        raise PolicyError("pyyaml is required to load policy files.") from exc

    policy_path = Path(path)
    if not policy_path.exists():
        raise PolicyError(f"Policy file not found: {path}")

    try:
        with policy_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as exc:
        raise PolicyError(f"Failed to parse policy file '{path}': {exc}") from exc

    if data is None:
        return Policy()

    if not isinstance(data, dict):
        raise PolicyError(f"Policy file '{path}' must be a YAML mapping.")

    valid_severities = {"BREAKING", "WARNING", "SAFE"}

    overrides: dict[str, str] = {}
    raw_overrides = data.get("overrides") or {}
    if not isinstance(raw_overrides, dict):
        raise PolicyError(f"'overrides' in '{path}' must be a mapping.")
    for key, val in raw_overrides.items():
        val_upper = str(val).upper()
        if val_upper not in valid_severities:
            raise PolicyError(
                f"Invalid severity '{val}' for override '{key}' in '{path}'. "
                f"Must be one of {valid_severities}."
            )
        overrides[str(key)] = val_upper

    ignore_tables: list[str] = []
    raw_tables = data.get("ignore_tables") or []
    if not isinstance(raw_tables, list):
        raise PolicyError(f"'ignore_tables' in '{path}' must be a list.")
    ignore_tables = [str(t) for t in raw_tables]

    ignore_columns: list[str] = []
    raw_columns = data.get("ignore_columns") or []
    if not isinstance(raw_columns, list):
        raise PolicyError(f"'ignore_columns' in '{path}' must be a list.")
    ignore_columns = [str(c) for c in raw_columns]

    return Policy(
        overrides=overrides,
        ignore_tables=ignore_tables,
        ignore_columns=ignore_columns,
    )


def apply_policy(result, policy: Policy):
    """
    Aplica overrides de política ao DiffResult como pós-processamento.
    Retorna um novo DiffResult com severidades e mudanças ajustadas.
    """
    if not policy.overrides and not policy.ignore_tables and not policy.ignore_columns:
        return result

    from driftbrake.models import DiffResult, Severity

    filtered = []
    for change in result.changes:
        # Ignorar tabelas
        if change.table_name in policy.ignore_tables:
            continue

        # Ignorar colunas (formato: "tabela.coluna")
        col_key = f"{change.table_name}.{change.column_name}" if change.column_name else None
        if col_key and col_key in policy.ignore_columns:
            continue

        # Aplicar override de severidade
        change_type_name = (
            change.change_type.value
            if hasattr(change.change_type, "value")
            else str(change.change_type)
        )
        if change_type_name in policy.overrides:
            from dataclasses import replace

            new_severity = Severity(policy.overrides[change_type_name])
            change = replace(
                change,
                severity=new_severity,
                description=f"{change.description} [overridden by policy: {new_severity.value}]",
            )

        filtered.append(change)

    return DiffResult(
        changes=filtered,
        compared_at=result.compared_at,
        expected_source=result.expected_source,
        current_source=result.current_source,
    )
