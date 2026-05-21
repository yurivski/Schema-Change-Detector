"""
Modelos de dados do DriftBrake.
Define as estruturas de dados utilizadas em toda a aplicação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    # Níveis de severidade para alterações de schema.
    BREAKING = "BREAKING"
    WARNING = "WARNING"
    SAFE = "SAFE"


class ChangeType(StrEnum):
    # Tipos de alterações de schema que podem ser detectadas.
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    TYPE_CHANGED = "type_changed"
    NULLABLE_CHANGED = "nullable_changed"
    DEFAULT_CHANGED = "default_changed"
    PRIMARY_KEY_CHANGED = "primary_key_changed"
    UNIQUE_CHANGED = "unique_changed"
    FOREIGN_KEY_CHANGED = "foreign_key_changed"
    FOREIGN_KEY_ADDED = "foreign_key_added"
    ORDINAL_POSITION_CHANGED = "ordinal_position_changed"
    POSSIBLE_RENAME = "possible_rename"


@dataclass
class ColumnSchema:
    # Representa o schema de uma única coluna.
    name: str
    type: str
    nullable: bool
    default: Any | None
    primary_key: bool
    unique: bool
    foreign_key: list[dict[str, Any]]
    ordinal_position: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "nullable": self.nullable,
            "default": self.default,
            "primary_key": self.primary_key,
            "unique": self.unique,
            "foreign_key": self.foreign_key,
            "ordinal_position": self.ordinal_position,
        }

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> ColumnSchema:
        return cls(
            name=name,
            type=data.get("type", "unknown"),
            nullable=data.get("nullable", True),
            default=data.get("default"),
            primary_key=data.get("primary_key", False),
            unique=data.get("unique", False),
            foreign_key=data.get("foreign_key", []),
            ordinal_position=data.get("ordinal_position", 0),
        )


@dataclass
class TableSchema:
    # Representa o schema de uma única tabela.
    name: str
    schema: str
    columns: dict[str, ColumnSchema] = field(default_factory=dict)
    indexes: list[str] = field(default_factory=list)
    check_constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": {col_name: col.to_dict() for col_name, col in self.columns.items()},
            "indexes": self.indexes,
            "check_constraints": self.check_constraints,
        }

    @classmethod
    def from_dict(cls, name: str, schema: str, data: dict[str, Any]) -> TableSchema:
        columns = {
            col_name: ColumnSchema.from_dict(col_name, col_data)
            for col_name, col_data in data.get("columns", {}).items()
        }
        return cls(
            name=name,
            schema=schema,
            columns=columns,
            indexes=data.get("indexes", []),
            check_constraints=data.get("check_constraints", []),
        )


@dataclass
class DatabaseSchema:
    # Representa o schema completo de um banco de dados.
    database_type: str
    generated_at: datetime
    schemas: dict[str, dict[str, TableSchema]] = field(default_factory=dict)

    def get_table(self, schema_name: str, table_name: str) -> TableSchema | None:
        return self.schemas.get(schema_name, {}).get(table_name)

    def all_tables(self) -> list[tuple[str, str, TableSchema]]:
        # Retorna todas as tabelas como tuplas (schema_name, table_name, table_schema).
        result = []
        for schema_name, tables in self.schemas.items():
            for table_name, table in tables.items():
                result.append((schema_name, table_name, table))
        return result


@dataclass
class SchemaChange:
    # Representa uma única alteração de schema detectada.
    change_type: ChangeType
    severity: Severity
    schema_name: str
    table_name: str
    column_name: str | None
    field_name: str | None
    old_value: Any
    new_value: Any
    description: str
    suggestion: str | None = None
    # Confiança da heurística (apenas para possible_rename): "low", "medium", "high"
    confidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "change_type": self.change_type.value,
            "severity": self.severity.value,
            "schema_name": self.schema_name,
            "table_name": self.table_name,
            "column_name": self.column_name,
            "field_name": self.field_name,
            "old_value": str(self.old_value) if self.old_value is not None else None,
            "new_value": str(self.new_value) if self.new_value is not None else None,
            "description": self.description,
            "suggestion": self.suggestion,
        }
        if self.confidence is not None:
            data["confidence"] = self.confidence
        return data


@dataclass
class DiffResult:
    # Resultado de uma operação de comparação de schema.
    changes: list[SchemaChange] = field(default_factory=list)
    compared_at: datetime = field(default_factory=datetime.now)
    expected_source: str = ""
    current_source: str = ""

    @property
    def breaking_changes(self) -> list[SchemaChange]:
        return [c for c in self.changes if c.severity == Severity.BREAKING]

    @property
    def warnings(self) -> list[SchemaChange]:
        return [c for c in self.changes if c.severity == Severity.WARNING]

    @property
    def safe_changes(self) -> list[SchemaChange]:
        return [c for c in self.changes if c.severity == Severity.SAFE]

    @property
    def total_breaking(self) -> int:
        return len(self.breaking_changes)

    @property
    def total_warnings(self) -> int:
        return len(self.warnings)

    @property
    def total_safe(self) -> int:
        return len(self.safe_changes)

    @property
    def has_breaking(self) -> bool:
        return self.total_breaking > 0

    @property
    def has_warnings(self) -> bool:
        return self.total_warnings > 0

    @property
    def is_compatible(self) -> bool:
        return not self.has_breaking

    def changes_by_severity(self, severity: Severity) -> list[SchemaChange]:
        return [c for c in self.changes if c.severity == severity]

    def changes_by_table(self) -> dict[str, list[SchemaChange]]:
        # Agrupa as alterações por nome de tabela.
        result: dict[str, list[SchemaChange]] = {}
        for change in self.changes:
            key = f"{change.schema_name}.{change.table_name}"
            if key not in result:
                result[key] = []
            result[key].append(change)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "compared_at": self.compared_at.isoformat(),
            "expected_source": self.expected_source,
            "current_source": self.current_source,
            "summary": {
                "total_breaking": self.total_breaking,
                "total_warnings": self.total_warnings,
                "total_safe": self.total_safe,
                "total_changes": len(self.changes),
                "is_compatible": self.is_compatible,
            },
            "changes": [c.to_dict() for c in self.changes],
        }
