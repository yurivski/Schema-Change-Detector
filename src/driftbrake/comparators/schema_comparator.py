from __future__ import annotations

from datetime import datetime

from driftbrake.classifiers.impact_classifier import ImpactClassifier
from driftbrake.classifiers.type_compatibility import classify_type_change
from driftbrake.models import (
    ChangeType,
    ColumnSchema,
    DatabaseSchema,
    DiffResult,
    SchemaChange,
    Severity,
    TableSchema,
)


# Comparador de schema (detecta diferenças entre dois objetos DatabaseSchema)
class SchemaComparator:
    """
    Detecta:
    - Tabelas adicionadas/removidas
    - Colunas adicionadas/removidas
    - Alterações de tipo
    - Alterações de nullable
    - Alterações de default
    - Alterações de chave primária
    - Alterações de restrição unique
    - Alterações de chave estrangeira
    - Alterações de posição ordinal
    - Possíveis renomeações de colunas (heurística)
    """

    def __init__(self, classifier: ImpactClassifier | None = None) -> None:
        self.classifier = classifier or ImpactClassifier()

    def compare(
        self,
        expected: DatabaseSchema,
        current: DatabaseSchema,
        expected_source: str = "contract",
        current_source: str = "database",
    ) -> DiffResult:
        """
        Compara o schema esperado com o schema atual do banco de dados.

        expected: O schema do arquivo de contrato (lock file).
        current: O schema atual do banco de dados.
        expected_source: Rótulo para a fonte esperada.
        current_source: Rótulo para a fonte atual.
        """
        changes: list[SchemaChange] = []

        all_schemas = set(expected.schemas.keys()) | set(current.schemas.keys())

        for schema_name in all_schemas:
            expected_tables = expected.schemas.get(schema_name, {})
            current_tables = current.schemas.get(schema_name, {})

            expected_table_names = set(expected_tables.keys())
            current_table_names = set(current_tables.keys())

            # Detecta tabelas removidas
            for table_name in expected_table_names - current_table_names:
                changes.append(
                    self.classifier.build_change(
                        change_type=ChangeType.TABLE_REMOVED,
                        severity=self.classifier.classify_table_removed(schema_name, table_name),
                        schema_name=schema_name,
                        table_name=table_name,
                        column_name=None,
                        field_name=None,
                        old_value=table_name,
                        new_value=None,
                        description=f"Table '{schema_name}.{table_name}' was removed.",
                    )
                )

            # Detecta tabelas adicionadas
            for table_name in current_table_names - expected_table_names:
                changes.append(
                    self.classifier.build_change(
                        change_type=ChangeType.TABLE_ADDED,
                        severity=self.classifier.classify_table_added(schema_name, table_name),
                        schema_name=schema_name,
                        table_name=table_name,
                        column_name=None,
                        field_name=None,
                        old_value=None,
                        new_value=table_name,
                        description=f"Table '{schema_name}.{table_name}' was added.",
                    )
                )

            # Compara tabelas existentes
            for table_name in expected_table_names & current_table_names:
                expected_table = expected_tables[table_name]
                current_table = current_tables[table_name]
                table_changes = self._compare_tables(
                    schema_name, table_name, expected_table, current_table
                )
                changes.extend(table_changes)

        return DiffResult(
            changes=changes,
            compared_at=datetime.now(),
            expected_source=expected_source,
            current_source=current_source,
        )

    def _compare_tables(
        self,
        schema_name: str,
        table_name: str,
        expected: TableSchema,
        current: TableSchema,
    ) -> list[SchemaChange]:
        changes: list[SchemaChange] = []

        expected_cols = set(expected.columns.keys())
        current_cols = set(current.columns.keys())

        removed_cols = expected_cols - current_cols
        added_cols = current_cols - expected_cols

        # Detecta possíveis renomeações antes de reportar adições/remoções separadamente
        rename_pairs = self._detect_possible_renames(expected, current, removed_cols, added_cols)
        renamed_removed = {pair[0] for pair in rename_pairs}
        renamed_added = {pair[1] for pair in rename_pairs}

        for old_col, new_col, confidence in rename_pairs:
            old_column = expected.columns[old_col]
            new_column = current.columns[new_col]
            change = self.classifier.build_change(
                change_type=ChangeType.POSSIBLE_RENAME,
                severity=self.classifier.classify_possible_rename(old_col, new_col),
                schema_name=schema_name,
                table_name=table_name,
                column_name=old_col,
                field_name=None,
                old_value=old_col,
                new_value=new_col,
                description=(
                    f"Column '{old_col}' removed and '{new_col}' added with "
                    f"compatible type ({old_column.type} -> {new_column.type}). "
                    "Possible rename."
                ),
                suggestion=(
                    f"If this is a rename, update the schema contract "
                    f"with the new column name '{new_col}'."
                ),
            )
            change.confidence = confidence
            changes.append(change)

        # Colunas removidas (que não fazem parte de uma renomeação)
        for col_name in removed_cols - renamed_removed:
            changes.append(
                self.classifier.build_change(
                    change_type=ChangeType.COLUMN_REMOVED,
                    severity=self.classifier.classify_column_removed(col_name),
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name=None,
                    old_value=col_name,
                    new_value=None,
                    description=f"Column '{col_name}' was removed from '{table_name}'.",
                )
            )

        # Colunas adicionadas (que não fazem parte de uma renomeação)
        for col_name in added_cols - renamed_added:
            col = current.columns[col_name]
            changes.append(
                self.classifier.build_change(
                    change_type=ChangeType.COLUMN_ADDED,
                    severity=self.classifier.classify_column_added(col),
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name=None,
                    old_value=None,
                    new_value=col_name,
                    description=self._describe_column_added(col_name, col),
                    suggestion=(
                        "Add the column with a default value or make it nullable "
                        "to avoid breaking existing consumers."
                        if not col.nullable and col.default is None
                        else None
                    ),
                )
            )

        # Compara colunas em comum
        for col_name in expected_cols & current_cols:
            exp_col = expected.columns[col_name]
            cur_col = current.columns[col_name]
            col_changes = self._compare_columns(schema_name, table_name, col_name, exp_col, cur_col)
            changes.extend(col_changes)

        return changes

    def _describe_column_added(self, col_name: str, col: ColumnSchema) -> str:
        if col.nullable:
            return f"Column '{col_name}' was added (nullable, safe)."
        if col.default is not None:
            return (
                f"Column '{col_name}' was added (NOT NULL with default='{col.default}', warning)."
            )
        return f"Column '{col_name}' was added (NOT NULL without default, breaking)."

    def _compare_columns(
        self,
        schema_name: str,
        table_name: str,
        col_name: str,
        expected: ColumnSchema,
        current: ColumnSchema,
    ) -> list[SchemaChange]:
        changes: list[SchemaChange] = []

        # Alteração de tipo
        if expected.type != current.type:
            severity = self.classifier.classify_type_change(expected.type, current.type)
            changes.append(
                self.classifier.build_change(
                    change_type=ChangeType.TYPE_CHANGED,
                    severity=severity,
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name="type",
                    old_value=expected.type,
                    new_value=current.type,
                    description=(
                        f"Column '{col_name}' type changed from '{expected.type}' "
                        f"to '{current.type}'."
                    ),
                )
            )

        # Alteração de nullable
        if expected.nullable != current.nullable:
            severity = self.classifier.classify_nullable_change(expected.nullable, current.nullable)
            if current.nullable:
                desc = f"Column '{col_name}' is now nullable (NOT NULL removed)."
            else:
                desc = f"Column '{col_name}' is now NOT NULL (nullable removed)."
            changes.append(
                self.classifier.build_change(
                    change_type=ChangeType.NULLABLE_CHANGED,
                    severity=severity,
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name="nullable",
                    old_value=expected.nullable,
                    new_value=current.nullable,
                    description=desc,
                )
            )

        # Alteração de default
        if expected.default != current.default:
            severity = self.classifier.classify_default_change(expected.default, current.default)
            changes.append(
                self.classifier.build_change(
                    change_type=ChangeType.DEFAULT_CHANGED,
                    severity=severity,
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name="default",
                    old_value=expected.default,
                    new_value=current.default,
                    description=(
                        f"Column '{col_name}' default changed from "
                        f"'{expected.default}' to '{current.default}'."
                    ),
                )
            )

        # Alteração de chave primária
        if expected.primary_key != current.primary_key:
            severity = self.classifier.classify_primary_key_change(
                expected.primary_key, current.primary_key
            )
            changes.append(
                self.classifier.build_change(
                    change_type=ChangeType.PRIMARY_KEY_CHANGED,
                    severity=severity,
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name="primary_key",
                    old_value=expected.primary_key,
                    new_value=current.primary_key,
                    description=f"Column '{col_name}' primary key status changed.",
                )
            )

        # Alteração de restrição unique
        if expected.unique != current.unique:
            severity = self.classifier.classify_unique_change(expected.unique, current.unique)
            changes.append(
                self.classifier.build_change(
                    change_type=ChangeType.UNIQUE_CHANGED,
                    severity=severity,
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name="unique",
                    old_value=expected.unique,
                    new_value=current.unique,
                    description=f"Column '{col_name}' unique constraint changed.",
                )
            )

        # Alteração de chave estrangeira
        old_fk_repr = [str(fk) for fk in expected.foreign_key]
        new_fk_repr = [str(fk) for fk in current.foreign_key]
        if old_fk_repr != new_fk_repr:
            severity = self.classifier.classify_foreign_key_change(
                expected.foreign_key, current.foreign_key
            )
            change_type = (
                ChangeType.FOREIGN_KEY_ADDED
                if not expected.foreign_key and current.foreign_key
                else ChangeType.FOREIGN_KEY_CHANGED
            )
            changes.append(
                self.classifier.build_change(
                    change_type=change_type,
                    severity=severity,
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name="foreign_key",
                    old_value=expected.foreign_key or None,
                    new_value=current.foreign_key or None,
                    description=f"Column '{col_name}' foreign key configuration changed.",
                )
            )

        # Alteração de posição ordinal
        if expected.ordinal_position != current.ordinal_position and (
            expected.ordinal_position != 0 and current.ordinal_position != 0
        ):
            severity = self.classifier.classify_ordinal_position_change(
                expected.ordinal_position, current.ordinal_position
            )
            changes.append(
                self.classifier.build_change(
                    change_type=ChangeType.ORDINAL_POSITION_CHANGED,
                    severity=severity,
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    field_name="ordinal_position",
                    old_value=expected.ordinal_position,
                    new_value=current.ordinal_position,
                    description=(
                        f"Column '{col_name}' ordinal position changed from "
                        f"{expected.ordinal_position} to {current.ordinal_position}."
                    ),
                )
            )

        return changes

    def _detect_possible_renames(
        self,
        expected: TableSchema,
        current: TableSchema,
        removed_cols: set[str],
        added_cols: set[str],
    ) -> list[tuple[str, str, str]]:
        """
        Detecta heuristicamente possíveis renomeações de colunas.
        Regras de confiança:
        high = nome similar + mesmo tipo + posição próxima (≤ 2)
        medium = mesmo tipo + posição próxima (≤ 2)
        low = apenas tipo compatível
        """
        pairs: list[tuple[str, str, str]] = []
        if not removed_cols or not added_cols:
            return pairs

        for removed in list(removed_cols):
            old_col = expected.columns[removed]
            best_match: str | None = None
            best_confidence: str = "low"

            for added in list(added_cols):
                if added in {p[1] for p in pairs}:
                    continue
                new_col = current.columns[added]
                compat = classify_type_change(old_col.type, new_col.type)
                if compat not in (Severity.SAFE, Severity.WARNING):
                    continue

                same_type = old_col.type == new_col.type
                close_position = abs(old_col.ordinal_position - new_col.ordinal_position) <= 2
                similar_name = self._names_are_similar(removed, added)

                if similar_name and same_type and close_position:
                    confidence = "high"
                elif same_type and close_position:
                    confidence = "medium"
                else:
                    confidence = "low"

                # Prioriza o melhor candidato encontrado
                if best_match is None or self._confidence_rank(confidence) > self._confidence_rank(
                    best_confidence
                ):
                    best_match = added
                    best_confidence = confidence

            if best_match is not None:
                pairs.append((removed, best_match, best_confidence))

        return pairs

    @staticmethod
    def _confidence_rank(confidence: str) -> int:
        # Converte nível de confiança para valor numérico para comparação.
        return {"low": 0, "medium": 1, "high": 2}.get(confidence, 0)

    @staticmethod
    def _names_are_similar(a: str, b: str) -> bool:
        # Verifica se dois nomes de colunas são semanticamente próximos.
        a_lower, b_lower = a.lower(), b.lower()
        # Prefixo ou sufixo comum de pelo menos 3 caracteres
        min_len = 3
        prefix_len = min(len(a_lower), len(b_lower))
        for length in range(prefix_len, min_len - 1, -1):
            if a_lower[:length] == b_lower[:length]:
                return True
        if len(a_lower) >= min_len and a_lower[-min_len:] == b_lower[-min_len:]:
            return True
        # Um nome contém o outro
        if a_lower in b_lower or b_lower in a_lower:
            return True
        return False
