# Classificador de impacto para alterações de schema.

from __future__ import annotations

from driftbrake.classifiers.type_compatibility import classify_type_change
from driftbrake.models import ChangeType, ColumnSchema, SchemaChange, Severity


class ImpactClassifier:
    """
    - Objetos removidos são sempre BREAKING.
    - Colunas nullable adicionadas são SAFE.
    - Colunas NOT NULL adicionadas sem default são BREAKING.
    - Alterações de tipo são avaliadas pela matriz de compatibilidade de tipos.
    """

    def __init__(self, custom_rules: dict | None = None) -> None:
        self.custom_rules = custom_rules or {}

    def classify_table_added(self, schema: str, table: str) -> Severity:
        return Severity.SAFE

    def classify_table_removed(self, schema: str, table: str) -> Severity:
        return Severity.BREAKING

    def classify_column_added(self, column: ColumnSchema) -> Severity:
        """
        - Adicionada nullable: SAFE
        - Adicionada NOT NULL com default: WARNING
        - Adicionada NOT NULL sem default: BREAKING
        """
        if column.nullable:
            return Severity.SAFE
        if column.default is not None:
            return Severity.WARNING
        return Severity.BREAKING

    def classify_column_removed(self, column_name: str) -> Severity:
        return Severity.BREAKING

    def classify_type_change(self, old_type: str, new_type: str) -> Severity:
        return classify_type_change(old_type, new_type)

    def classify_nullable_change(self, old_nullable: bool, new_nullable: bool) -> Severity:
        if not old_nullable and new_nullable:
            # NOT NULL removido -> nullable permitido: WARNING (afrouxamento)
            return Severity.WARNING
        if old_nullable and not new_nullable:
            # nullable removido -> NOT NULL adicionado: BREAKING
            return Severity.BREAKING
        return Severity.SAFE

    def classify_default_change(self, old_default: object, new_default: object) -> Severity:
        return Severity.WARNING

    def classify_primary_key_change(self, old_pk: bool, new_pk: bool) -> Severity:
        return Severity.BREAKING

    def classify_unique_change(self, old_unique: bool, new_unique: bool) -> Severity:
        return Severity.WARNING

    def classify_foreign_key_change(self, old_fk: list, new_fk: list) -> Severity:
        old_has = bool(old_fk)
        new_has = bool(new_fk)
        if not old_has and new_has:
            # FK adicionada
            return Severity.WARNING
        # FK alterada ou removida
        return Severity.BREAKING

    def classify_ordinal_position_change(self, old_pos: int, new_pos: int) -> Severity:
        return Severity.WARNING

    def classify_possible_rename(self, removed_col: str, added_col: str) -> Severity:
        return Severity.WARNING

    def build_change(
        self,
        change_type: ChangeType,
        severity: Severity,
        schema_name: str,
        table_name: str,
        column_name: str | None,
        field_name: str | None,
        old_value: object,
        new_value: object,
        description: str,
        suggestion: str | None = None,
    ) -> SchemaChange:
        return SchemaChange(
            change_type=change_type,
            severity=severity,
            schema_name=schema_name,
            table_name=table_name,
            column_name=column_name,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            description=description,
            suggestion=suggestion,
        )
