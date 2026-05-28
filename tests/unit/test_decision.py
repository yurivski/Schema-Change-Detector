"""
Testes parametrizados da função decide(), cobre toda a matriz de decisão.
Pra evitar que o arquivo fique muito grande, apenas as chamadas com argumentos
acima de 100 caracteres terão quebras de linhas.
"""

from __future__ import annotations

import pytest

from driftbrake.decision import decide
from driftbrake.models import ChangeType, DiffResult, SchemaChange, Severity

# helpers


def _change(severity: Severity) -> SchemaChange:
    return SchemaChange(
        change_type=ChangeType.COLUMN_REMOVED,
        severity=severity,
        schema_name="public",
        table_name="users",
        column_name="email",
        field_name=None,
        old_value="text",
        new_value=None,
        description="Column removed",
    )


def _result(*severities: Severity) -> DiffResult:
    return DiffResult(changes=[_change(s) for s in severities])


def _empty_result() -> DiffResult:
    return DiffResult(changes=[])


# matriz de decisão
@pytest.mark.parametrize(
    "severity,fail_on,ask_on,interactive,expected_action",
    [
        # nenhuma mudança -> release
        ("none", ["BREAKING"], ["WARNING"], True, "release"),
        # safe, fail_on=BREAKING -> release
        ("safe", ["BREAKING"], ["WARNING"], False, "release"),
        # warning, interactive=True, ask_on=WARNING -> ask
        ("warning", ["BREAKING"], ["WARNING"], True, "ask"),
        # warning, interactive=False, ask_on=WARNING -> release
        ("warning", ["BREAKING"], ["WARNING"], False, "release"),
        # warning, fail_on inclui WARNING -> block
        ("warning", ["BREAKING", "WARNING"], [], True, "block"),
        # breaking, fail_on=BREAKING -> block
        ("breaking", ["BREAKING"], ["WARNING"], True, "block"),
        # safe, fail_on=SAFE -> block (strict opt-in)
        ("safe", ["SAFE"], [], True, "block"),
        # safe, ask_on=SAFE, interactive=True -> ask (strict opt-in)
        ("safe", [], ["SAFE"], True, "ask"),
    ],
)
def test_decision_matrix(severity, fail_on, ask_on, interactive, expected_action):
    if severity == "none":
        result = _empty_result()
    elif severity == "safe":
        result = _result(Severity.SAFE)
    elif severity == "warning":
        result = _result(Severity.WARNING)
    else:
        result = _result(Severity.BREAKING)

    decision = decide(
        result=result,
        fail_on=fail_on,
        ask_on=ask_on,
        interactive_effective=interactive,
    )
    assert decision.action == expected_action


# testes de propriedades do Decision


def test_decision_block_has_exit_code():
    result = _result(Severity.BREAKING)
    d = decide(result=result, fail_on=["BREAKING"], ask_on=[], interactive_effective=False)
    assert d.action == "block"
    assert d.exit_code == 2


def test_decision_release_no_exit_code():
    result = _empty_result()
    d = decide(result=result, fail_on=["BREAKING"], ask_on=["WARNING"], interactive_effective=True)
    assert d.action == "release"
    assert d.exit_code is None


def test_decision_severity_none_on_empty():
    d = decide(
        result=_empty_result(),
        fail_on=["BREAKING"],
        ask_on=["WARNING"],
        interactive_effective=True,
    )
    assert d.severity == "none"


def test_decision_severity_matches_highest():
    # resultado com BREAKING e WARNING — highest é BREAKING
    result = DiffResult(changes=[_change(Severity.WARNING), _change(Severity.BREAKING)])
    d = decide(result=result, fail_on=["BREAKING"], ask_on=["WARNING"], interactive_effective=True)
    assert d.severity == "breaking"
    assert d.action == "block"


def test_decision_is_frozen():
    d = decide(result=_empty_result(), fail_on=[], ask_on=[], interactive_effective=False)
    with pytest.raises((AttributeError, TypeError)):
        d.action = "block"  # type: ignore[misc]


# TTY detection (indireto via resolve_interactive)


def test_warning_non_interactive_not_in_ask_on_releases():
    result = _result(Severity.WARNING)
    d = decide(result=result, fail_on=["BREAKING"], ask_on=[], interactive_effective=False)
    assert d.action == "release"


def test_breaking_non_interactive_still_blocks():
    result = _result(Severity.BREAKING)
    d = decide(result=result, fail_on=["BREAKING"], ask_on=[], interactive_effective=False)
    assert d.action == "block"
