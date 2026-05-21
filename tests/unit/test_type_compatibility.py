# Testes unitários para a matriz de compatibilidade de tipos.


from driftbrake.classifiers.type_compatibility import classify_type_change
from driftbrake.models import Severity


class TestVarcharChanges:
    def test_varchar_widening_is_safe(self):
        assert classify_type_change("VARCHAR(50)", "VARCHAR(100)") == Severity.SAFE

    def test_varchar_narrowing_is_breaking(self):
        assert classify_type_change("VARCHAR(100)", "VARCHAR(50)") == Severity.BREAKING

    def test_varchar_same_length_is_safe(self):
        assert classify_type_change("VARCHAR(100)", "VARCHAR(100)") == Severity.SAFE

    def test_varchar_to_text_is_safe(self):
        assert classify_type_change("VARCHAR(100)", "TEXT") == Severity.SAFE

    def test_text_to_varchar_is_breaking(self):
        assert classify_type_change("TEXT", "VARCHAR(100)") == Severity.BREAKING


class TestIntegerChanges:
    def test_integer_to_bigint_is_warning(self):
        assert classify_type_change("integer", "bigint") == Severity.WARNING

    def test_bigint_to_integer_is_breaking(self):
        assert classify_type_change("bigint", "integer") == Severity.BREAKING

    def test_smallint_to_integer_is_safe(self):
        assert classify_type_change("smallint", "integer") == Severity.SAFE

    def test_smallint_to_bigint_is_safe(self):
        assert classify_type_change("smallint", "bigint") == Severity.SAFE

    def test_integer_to_smallint_is_breaking(self):
        assert classify_type_change("integer", "smallint") == Severity.BREAKING


class TestNumericChanges:
    def test_numeric_precision_widening_is_safe(self):
        assert classify_type_change("NUMERIC(10,2)", "NUMERIC(12,2)") == Severity.SAFE

    def test_numeric_precision_narrowing_is_breaking(self):
        assert classify_type_change("NUMERIC(12,2)", "NUMERIC(10,2)") == Severity.BREAKING

    def test_numeric_same_is_safe(self):
        assert classify_type_change("NUMERIC(10,2)", "NUMERIC(10,2)") == Severity.SAFE

    def test_numeric_to_text_is_breaking(self):
        assert classify_type_change("numeric", "text") == Severity.BREAKING

    def test_text_to_numeric_is_breaking(self):
        assert classify_type_change("text", "numeric") == Severity.BREAKING


class TestDateTimeChanges:
    def test_date_to_timestamp_is_warning(self):
        assert classify_type_change("date", "timestamp") == Severity.WARNING

    def test_timestamp_to_date_is_breaking(self):
        assert classify_type_change("timestamp", "date") == Severity.BREAKING

    def test_timestamp_to_timestamptz_is_warning(self):
        assert classify_type_change("timestamp", "timestamptz") == Severity.WARNING


class TestIdenticalTypes:
    def test_same_type_is_safe(self):
        assert classify_type_change("INTEGER", "INTEGER") == Severity.SAFE
        assert classify_type_change("TEXT", "TEXT") == Severity.SAFE
        assert classify_type_change("BOOLEAN", "BOOLEAN") == Severity.SAFE

    def test_same_type_case_insensitive(self):
        assert classify_type_change("integer", "INTEGER") == Severity.SAFE
        assert classify_type_change("Varchar(50)", "VARCHAR(50)") == Severity.SAFE


class TestBooleanChanges:
    def test_boolean_to_integer_is_breaking(self):
        assert classify_type_change("boolean", "integer") == Severity.BREAKING

    def test_integer_to_boolean_is_breaking(self):
        assert classify_type_change("integer", "boolean") == Severity.BREAKING


class TestUnknownTypeFallback:
    def test_completely_different_types_are_breaking(self):
        assert classify_type_change("uuid", "bytea") == Severity.BREAKING
        assert classify_type_change("jsonb", "text") == Severity.BREAKING
