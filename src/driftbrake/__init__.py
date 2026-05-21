"""
DriftBrake
=========

A schema contract guard for data pipelines.
Detects, classifies, and reports schema changes in PostgreSQL databases.

Quick start:
    from driftbrake import SchemaGuard

    SchemaGuard.from_env(
        contract_path="schema.lock.json",
        fail_on=["BREAKING"],
    ).assert_compatible()
"""

from driftbrake.classifiers.impact_classifier import ImpactClassifier
from driftbrake.comparators.schema_comparator import SchemaComparator
from driftbrake.exceptions import (
    BreakingSchemaChangeError,
    ConfigurationError,
    SchemaConnectionError,
    SchemaContractNotFoundError,
    SchemaDetectorError,
)
from driftbrake.guard import SchemaGuard
from driftbrake.models import (
    ChangeType,
    ColumnSchema,
    DatabaseSchema,
    DiffResult,
    SchemaChange,
    Severity,
    TableSchema,
)
from driftbrake.readers.json_reader import JsonSchemaReader
from driftbrake.readers.postgres import PostgresSchemaReader

__version__ = "0.2.0"

__all__ = [
    # High-level API
    "SchemaGuard",
    # Comparators and classifiers
    "SchemaComparator",
    "ImpactClassifier",
    # Readers
    "PostgresSchemaReader",
    "JsonSchemaReader",
    # Models
    "DatabaseSchema",
    "TableSchema",
    "ColumnSchema",
    "SchemaChange",
    "DiffResult",
    "Severity",
    "ChangeType",
    # Exceptions
    "SchemaDetectorError",
    "SchemaContractNotFoundError",
    "SchemaConnectionError",
    "BreakingSchemaChangeError",
    "ConfigurationError",
]
