"""
Testes unitários para SchemaComparator.

Todos os testes usam fixtures em memória, sem nenhuma conexão com banco de dados.
"""

from datetime import datetime
from pathlib import Path

from driftbrake.comparators.schema_comparator import SchemaComparator
from driftbrake.models import (
    ChangeType,
    ColumnSchema,
    DatabaseSchema,
    Severity,
    TableSchema,
)
from driftbrake.readers.json_reader import JsonSchemaReader


def _make_db(tables: dict[str, TableSchema], schema: str = "public") -> DatabaseSchema:
    return DatabaseSchema(
        database_type="postgresql",
        generated_at=datetime.now(),
        schemas={schema: tables},
    )


def _make_table(
    name: str, schema: str = "public", columns: dict[str, ColumnSchema] | None = None
) -> TableSchema:
    return TableSchema(
        name=name,
        schema=schema,
        columns=columns or {},
        indexes=[],
        check_constraints=[],
    )


def _make_col(
    name: str,
    type_: str = "INTEGER",
    nullable: bool = True,
    default=None,
    primary_key: bool = False,
    unique: bool = False,
    foreign_key: list | None = None,
    ordinal_position: int = 1,
) -> ColumnSchema:
    return ColumnSchema(
        name=name,
        type=type_,
        nullable=nullable,
        default=default,
        primary_key=primary_key,
        unique=unique,
        foreign_key=foreign_key or [],
        ordinal_position=ordinal_position,
    )


comparator = SchemaComparator()


class TestColumnRemoved:
    def test_column_removed_is_breaking(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "id": _make_col("id"),
                        "name": _make_col("name"),
                    },
                )
            }
        )
        current = _make_db({"t": _make_table("t", columns={"id": _make_col("id")})})
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.COLUMN_REMOVED]
        assert len(changes) >= 1
        assert all(c.severity == Severity.BREAKING for c in changes)
        cols = [c.column_name for c in changes]
        assert "name" in cols


class TestColumnAddedNullable:
    def test_column_added_nullable_is_safe(self):
        expected = _make_db({"t": _make_table("t", columns={"id": _make_col("id")})})
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "id": _make_col("id"),
                        "new_col": _make_col("new_col", nullable=True),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [
            c
            for c in result.changes
            if c.change_type == ChangeType.COLUMN_ADDED and c.column_name == "new_col"
        ]
        assert len(changes) == 1
        assert changes[0].severity == Severity.SAFE


class TestColumnAddedNotNullWithoutDefault:
    def test_column_added_not_null_no_default_is_breaking(self):
        expected = _make_db({"t": _make_table("t", columns={"id": _make_col("id")})})
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "id": _make_col("id"),
                        "required": _make_col("required", nullable=False, default=None),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [
            c
            for c in result.changes
            if c.change_type == ChangeType.COLUMN_ADDED and c.column_name == "required"
        ]
        assert len(changes) == 1
        assert changes[0].severity == Severity.BREAKING


class TestColumnAddedNotNullWithDefault:
    def test_column_added_not_null_with_default_is_warning(self):
        expected = _make_db({"t": _make_table("t", columns={"id": _make_col("id")})})
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "id": _make_col("id"),
                        "required": _make_col("required", nullable=False, default="'default_val'"),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [
            c
            for c in result.changes
            if c.change_type == ChangeType.COLUMN_ADDED and c.column_name == "required"
        ]
        assert len(changes) == 1
        assert changes[0].severity == Severity.WARNING


class TestTypeChanged:
    def test_type_changed_varchar_narrowing_is_breaking(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "name": _make_col("name", type_="VARCHAR(100)"),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "name": _make_col("name", type_="VARCHAR(50)"),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.TYPE_CHANGED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.BREAKING

    def test_type_changed_varchar_widening_is_safe(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "name": _make_col("name", type_="VARCHAR(50)"),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "name": _make_col("name", type_="VARCHAR(100)"),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.TYPE_CHANGED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.SAFE

    def test_type_changed_integer_to_bigint_is_warning(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "val": _make_col("val", type_="integer"),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "val": _make_col("val", type_="bigint"),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.TYPE_CHANGED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.WARNING


class TestNullableChanged:
    def test_not_null_added_is_breaking(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "col": _make_col("col", nullable=True),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "col": _make_col("col", nullable=False),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.NULLABLE_CHANGED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.BREAKING

    def test_not_null_removed_is_warning(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "col": _make_col("col", nullable=False),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "col": _make_col("col", nullable=True),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.NULLABLE_CHANGED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.WARNING


class TestPrimaryKeyChanged:
    def test_primary_key_changed_is_breaking(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "id": _make_col("id", primary_key=True),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "id": _make_col("id", primary_key=False),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.PRIMARY_KEY_CHANGED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.BREAKING


class TestUniqueChanged:
    def test_unique_changed_is_warning(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "email": _make_col("email", unique=True),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "email": _make_col("email", unique=False),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.UNIQUE_CHANGED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.WARNING


class TestForeignKeyChanged:
    def test_foreign_key_added_is_warning(self):
        fk = [
            {
                "constrained_columns": ["customer_id"],
                "referred_table": "customers",
                "referred_columns": ["id"],
            }
        ]
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "customer_id": _make_col("customer_id", foreign_key=[]),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "customer_id": _make_col("customer_id", foreign_key=fk),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        fk_types = (ChangeType.FOREIGN_KEY_CHANGED, ChangeType.FOREIGN_KEY_ADDED)
        changes = [c for c in result.changes if c.change_type in fk_types]
        assert len(changes) == 1
        assert changes[0].severity == Severity.WARNING

    def test_foreign_key_changed_is_breaking(self):
        fk_old = [
            {"constrained_columns": ["cid"], "referred_table": "a", "referred_columns": ["id"]}
        ]
        fk_new = [
            {"constrained_columns": ["cid"], "referred_table": "b", "referred_columns": ["id"]}
        ]
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "cid": _make_col("cid", foreign_key=fk_old),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "cid": _make_col("cid", foreign_key=fk_new),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        fk_types = (ChangeType.FOREIGN_KEY_CHANGED, ChangeType.FOREIGN_KEY_ADDED)
        changes = [c for c in result.changes if c.change_type in fk_types]
        assert len(changes) == 1
        assert changes[0].severity == Severity.BREAKING


class TestOrdinalPositionChanged:
    def test_ordinal_position_changed_is_warning(self):
        expected = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "col": _make_col("col", ordinal_position=2),
                    },
                )
            }
        )
        current = _make_db(
            {
                "t": _make_table(
                    "t",
                    columns={
                        "col": _make_col("col", ordinal_position=5),
                    },
                )
            }
        )
        result = comparator.compare(expected, current)
        changes = [
            c for c in result.changes if c.change_type == ChangeType.ORDINAL_POSITION_CHANGED
        ]
        assert len(changes) == 1
        assert changes[0].severity == Severity.WARNING


class TestTableAddedRemoved:
    def test_table_removed_is_breaking(self):
        expected = _make_db({"t": _make_table("t"), "dropped": _make_table("dropped")})
        current = _make_db({"t": _make_table("t")})
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.TABLE_REMOVED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.BREAKING
        assert changes[0].table_name == "dropped"

    def test_table_added_is_safe(self):
        expected = _make_db({"t": _make_table("t")})
        current = _make_db({"t": _make_table("t"), "new_t": _make_table("new_t")})
        result = comparator.compare(expected, current)
        changes = [c for c in result.changes if c.change_type == ChangeType.TABLE_ADDED]
        assert len(changes) == 1
        assert changes[0].severity == Severity.SAFE


class TestNoChanges:
    def test_identical_schemas_produce_no_changes(self):
        col = _make_col("id", type_="INTEGER", nullable=False, primary_key=True)
        expected = _make_db({"t": _make_table("t", columns={"id": col})})
        current = _make_db({"t": _make_table("t", columns={"id": col})})
        result = comparator.compare(expected, current)
        assert result.changes == []
        assert result.is_compatible


class TestFixtureFiles:
    # Testes de integração usando os arquivos de fixture JSON.

    def test_fixture_comparison_produces_expected_change_types(self):

        fixtures = Path(__file__).parent.parent / "fixtures"
        before = JsonSchemaReader(fixtures / "schema_before.json").read()
        after = JsonSchemaReader(fixtures / "schema_after.json").read()

        result = comparator.compare(before, after)

        change_types = {c.change_type for c in result.changes}
        # A tabela products foi removida
        assert ChangeType.TABLE_REMOVED in change_types
        # new_table foi adicionada
        assert ChangeType.TABLE_ADDED in change_types
        # old_column (TEXT) e new_nullable_col (TEXT) têm tipos compatíveis,
        # então o comparador detecta uma possível renomeação em vez de remoção/adição separada.
        possible_rename = [
            c
            for c in result.changes
            if c.change_type == ChangeType.POSSIBLE_RENAME and c.column_name == "old_column"
        ]
        column_removed = [
            c
            for c in result.changes
            if c.change_type == ChangeType.COLUMN_REMOVED and c.column_name == "old_column"
        ]
        # Ou uma renomeação foi detectada OU a coluna foi classificada como removida
        assert len(possible_rename) >= 1 or len(column_removed) >= 1
        # required_col foi adicionada NOT NULL sem default: BREAKING
        col_added_breaking = [
            c
            for c in result.changes
            if c.change_type == ChangeType.COLUMN_ADDED and c.column_name == "required_col"
        ]
        assert len(col_added_breaking) == 1
        assert col_added_breaking[0].severity == Severity.BREAKING
        # required_with_default foi adicionada NOT NULL com default: WARNING
        col_added_warning = [
            c
            for c in result.changes
            if c.change_type == ChangeType.COLUMN_ADDED and c.column_name == "required_with_default"
        ]
        assert len(col_added_warning) == 1
        assert col_added_warning[0].severity == Severity.WARNING
        # name VARCHAR(100) -> VARCHAR(50): BREAKING
        name_type_change = [
            c
            for c in result.changes
            if c.change_type == ChangeType.TYPE_CHANGED and c.column_name == "name"
        ]
        assert len(name_type_change) == 1
        assert name_type_change[0].severity == Severity.BREAKING
        # email nullable alterado de True -> False: BREAKING
        email_nullable = [
            c
            for c in result.changes
            if c.change_type == ChangeType.NULLABLE_CHANGED and c.column_name == "email"
        ]
        assert len(email_nullable) == 1
        assert email_nullable[0].severity == Severity.BREAKING
