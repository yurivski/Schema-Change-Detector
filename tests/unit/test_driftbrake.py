"""
Testes de integração de DriftBrake.protect() usando FakePrompter e RecordingReporter.
Pra evitar que o arquivo fique muito grande, apenas as chamadas com argumentos
acima de 100 caracteres terão quebras de linhas.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from driftbrake.driftbrake import DriftBrake
from driftbrake.exceptions import (
    BreakingChangesDetected,
    ContractMissingError,
    MissingDatabaseURL,
    UserAborted,
)
from driftbrake.models import ChangeType, DiffResult, SchemaChange, Severity

# Doubles de teste


class RecordingReporter:
    """Registra todas as chamadas para inspeção em testes."""

    def __init__(self):
        self.calls: list[str] = []

    def on_no_drift(self, result):
        self.calls.append("on_no_drift")

    def on_safe(self, result):
        self.calls.append("on_safe")

    def on_warning(self, result):
        self.calls.append("on_warning")

    def on_breaking(self, result):
        self.calls.append("on_breaking")

    def on_contract_missing(self, contract_path):
        self.calls.append("on_contract_missing")

    def on_contract_created(self, contract_path):
        self.calls.append("on_contract_created")

    def on_released(self):
        self.calls.append("on_released")

    def on_blocked(self, reason):
        self.calls.append("on_blocked")


class FakePrompter:
    """Prompter determinístico para testes."""

    def __init__(self, answer: bool = True):
        self.answer = answer
        self.calls: list[str] = []

    def confirm_create_contract(self, contract_path):
        self.calls.append("confirm_create_contract")
        return self.answer

    def confirm_continue_with_warnings(self, result):
        self.calls.append("confirm_continue_with_warnings")
        return self.answer

    def confirm_continue_with_safe(self, result):
        self.calls.append("confirm_continue_with_safe")
        return self.answer


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


def _make_db(
    *,
    contract_exists: bool = True,
    diff_result: DiffResult | None = None,
    interactive: bool = False,
    fail_on: list[str] | None = None,
    ask_on: list[str] | None = None,
    auto_init: bool = True,
    prompter_answer: bool = True,
) -> tuple[DriftBrake, RecordingReporter, FakePrompter]:
    reporter = RecordingReporter()
    prompter = FakePrompter(answer=prompter_answer)
    db = DriftBrake(
        database_url="postgresql://fake:fake@localhost/fake",
        contract_path="schema.lock.json",
        auto_init=auto_init,
        interactive=interactive,
        fail_on=fail_on or ["BREAKING"],
        ask_on=ask_on or ["WARNING"],
        reporter=reporter,
        prompter=prompter,
    )
    # injeta _interactive já resolvido
    db._interactive = interactive

    # patch _contract_exists
    db._contract_exists = lambda: contract_exists
    db._create_contract = MagicMock()

    # patch guard.check
    if diff_result is not None:
        db.guard.check = MagicMock(return_value=diff_result)
        db.guard.save_reports = MagicMock()

    return db, reporter, prompter


# Tabela de decisão


def test_row1_contract_missing_auto_init_false():
    """contrato ausente, auto_init=False -> ContractMissingError (exit 4)."""
    db, reporter, _ = _make_db(contract_exists=False, auto_init=False)
    with pytest.raises(ContractMissingError) as exc_info:
        db.protect()
    assert exc_info.value.exit_code == 4
    assert "on_contract_missing" in reporter.calls


def test_row2_contract_missing_auto_init_true_interactive_yes():
    """Contrato ausente + auto_init + interactive + confirma=True -> cria."""
    db, reporter, prompter = _make_db(
        contract_exists=False, auto_init=True, interactive=True, prompter_answer=True
    )
    result = db.protect()
    assert result is None
    assert "confirm_create_contract" in prompter.calls
    db._create_contract.assert_called_once()
    assert "on_contract_created" in reporter.calls


def test_row3_contract_missing_auto_init_true_interactive_no():
    """Contrato ausente + auto_init + interactive + confirma=False -> UserAborted (exit 7)."""
    db, reporter, prompter = _make_db(
        contract_exists=False, auto_init=True, interactive=True, prompter_answer=False
    )
    with pytest.raises(UserAborted) as exc_info:
        db.protect()
    assert exc_info.value.exit_code == 7


def test_row4_contract_missing_auto_init_true_non_interactive():
    """Contrato ausente + auto_init + non-interactive -> cria sem perguntar."""
    db, reporter, prompter = _make_db(contract_exists=False, auto_init=True, interactive=False)
    result = db.protect()
    assert result is None
    assert "confirm_create_contract" not in prompter.calls
    db._create_contract.assert_called_once()


def test_row5_no_drift():
    """sem mudanças -> release."""
    result_obj = DiffResult(changes=[])
    db, reporter, _ = _make_db(diff_result=result_obj)
    result = db.protect()
    assert result is not None
    assert "on_no_drift" in reporter.calls
    assert "on_released" in reporter.calls


def test_row6_safe_default_config():
    """SAFE, fail_on=BREAKING -> release."""
    result_obj = DiffResult(changes=[_change(Severity.SAFE)])
    db, reporter, _ = _make_db(diff_result=result_obj, fail_on=["BREAKING"], ask_on=["WARNING"])
    result = db.protect()
    assert result is not None
    assert "on_safe" in reporter.calls
    assert "on_released" in reporter.calls


def test_row7_warning_interactive_yes():
    """WARNING, interactive=True, confirma=True -> release."""
    result_obj = DiffResult(changes=[_change(Severity.WARNING)])
    db, reporter, prompter = _make_db(
        diff_result=result_obj,
        interactive=True,
        fail_on=["BREAKING"],
        ask_on=["WARNING"],
        prompter_answer=True,
    )
    result = db.protect()
    assert result is not None
    assert "confirm_continue_with_warnings" in prompter.calls
    assert "on_released" in reporter.calls


def test_row8_warning_interactive_no():
    """WARNING, interactive=True, confirma=False -> UserAborted (exit 7)."""
    result_obj = DiffResult(changes=[_change(Severity.WARNING)])
    db, reporter, prompter = _make_db(
        diff_result=result_obj,
        interactive=True,
        fail_on=["BREAKING"],
        ask_on=["WARNING"],
        prompter_answer=False,
    )
    with pytest.raises(UserAborted) as exc_info:
        db.protect()
    assert exc_info.value.exit_code == 7


def test_row9_warning_non_interactive_default_fail_on():
    """WARNING, interactive=False, fail_on=BREAKING -> release com aviso."""
    result_obj = DiffResult(changes=[_change(Severity.WARNING)])
    db, reporter, _ = _make_db(
        diff_result=result_obj,
        interactive=False,
        fail_on=["BREAKING"],
        ask_on=["WARNING"],
    )
    result = db.protect()
    assert result is not None
    assert "on_warning" in reporter.calls
    assert "on_released" in reporter.calls


def test_row10_warning_in_fail_on():
    """WARNING, fail_on=[BREAKING, WARNING] -> BreakingChangesDetected (exit 2)."""
    result_obj = DiffResult(changes=[_change(Severity.WARNING)])
    db, reporter, _ = _make_db(
        diff_result=result_obj,
        fail_on=["BREAKING", "WARNING"],
        ask_on=[],
    )
    with pytest.raises(BreakingChangesDetected) as exc_info:
        db.protect()
    assert exc_info.value.exit_code == 2
    assert "on_blocked" in reporter.calls


def test_row11_breaking_blocks():
    """BREAKING, fail_on=[BREAKING] -> BreakingChangesDetected (exit 2)."""
    result_obj = DiffResult(changes=[_change(Severity.BREAKING)])
    db, reporter, _ = _make_db(diff_result=result_obj, fail_on=["BREAKING"])
    with pytest.raises(BreakingChangesDetected) as exc_info:
        db.protect()
    assert exc_info.value.exit_code == 2
    assert "on_breaking" in reporter.calls
    assert "on_blocked" in reporter.calls


def test_row12_safe_in_fail_on_blocks():
    """SAFE, fail_on=[SAFE] -> BreakingChangesDetected (exit 2) — opt-in estrito."""
    result_obj = DiffResult(changes=[_change(Severity.SAFE)])
    db, reporter, _ = _make_db(
        diff_result=result_obj,
        fail_on=["SAFE"],
        ask_on=[],
    )
    with pytest.raises(BreakingChangesDetected) as exc_info:
        db.protect()
    assert exc_info.value.exit_code == 2


def test_row13_safe_in_ask_on_interactive_yes():
    """SAFE, ask_on=[SAFE], interactive=True, confirma=True -> release — opt-in estrito."""
    result_obj = DiffResult(changes=[_change(Severity.SAFE)])
    db, reporter, prompter = _make_db(
        diff_result=result_obj,
        interactive=True,
        fail_on=[],
        ask_on=["SAFE"],
        prompter_answer=True,
    )
    result = db.protect()
    assert result is not None
    assert "confirm_continue_with_safe" in prompter.calls
    assert "on_released" in reporter.calls


# Cenário misto: múltiplas severidades


def test_mixed_severities_all_reporter_methods_called():
    """BREAKING+WARNING+SAFE -> on_safe, on_warning e on_breaking são todos invocados."""
    result_obj = DiffResult(
        changes=[
            _change(Severity.SAFE),
            _change(Severity.WARNING),
            _change(Severity.BREAKING),
        ]
    )
    db, reporter, _ = _make_db(diff_result=result_obj, fail_on=["BREAKING"])
    with pytest.raises(BreakingChangesDetected):
        db.protect()
    assert "on_safe" in reporter.calls
    assert "on_warning" in reporter.calls
    assert "on_breaking" in reporter.calls
    assert "on_blocked" in reporter.calls


def test_mixed_breaking_warning_no_safe_reporter():
    """BREAKING+WARNING -> on_warning e on_breaking chamados; on_safe não."""
    result_obj = DiffResult(
        changes=[
            _change(Severity.WARNING),
            _change(Severity.BREAKING),
        ]
    )
    db, reporter, _ = _make_db(diff_result=result_obj, fail_on=["BREAKING"])
    with pytest.raises(BreakingChangesDetected):
        db.protect()
    assert "on_safe" not in reporter.calls
    assert "on_warning" in reporter.calls
    assert "on_breaking" in reporter.calls


# protect_or_exit


def test_protect_or_exit_translates_breaking_to_sys_exit():
    result_obj = DiffResult(changes=[_change(Severity.BREAKING)])
    db, _, _ = _make_db(diff_result=result_obj, fail_on=["BREAKING"])
    with pytest.raises(SystemExit) as exc_info:
        db.protect_or_exit()
    assert exc_info.value.code == 2


def test_protect_or_exit_returns_result_on_success():
    result_obj = DiffResult(changes=[])
    db, _, _ = _make_db(diff_result=result_obj)
    result = db.protect_or_exit()
    assert result is not None


# BreakingChangesDetected carrega o result


def test_breaking_changes_detected_carries_result():
    result_obj = DiffResult(changes=[_change(Severity.BREAKING)])
    db, _, _ = _make_db(diff_result=result_obj, fail_on=["BREAKING"])
    with pytest.raises(BreakingChangesDetected) as exc_info:
        db.protect()
    assert exc_info.value.result is result_obj


# TTY detection


def test_resolve_interactive_auto_non_tty():
    db = DriftBrake.__new__(DriftBrake)
    db._interactive_raw = "auto"
    with patch("sys.stdin") as mock_stdin, patch("sys.stdout") as mock_stdout:
        mock_stdin.isatty.return_value = False
        mock_stdout.isatty.return_value = True
        assert db._resolve_interactive() is False


def test_resolve_interactive_auto_tty():
    db = DriftBrake.__new__(DriftBrake)
    db._interactive_raw = "auto"
    with patch("sys.stdin") as mock_stdin, patch("sys.stdout") as mock_stdout:
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        assert db._resolve_interactive() is True


def test_resolve_interactive_explicit_true():
    db = DriftBrake.__new__(DriftBrake)
    db._interactive_raw = True
    assert db._resolve_interactive() is True


def test_resolve_interactive_explicit_false():
    db = DriftBrake.__new__(DriftBrake)
    db._interactive_raw = False
    assert db._resolve_interactive() is False


# run_from_env


def test_run_from_env_missing_database_url_exits_5(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    with pytest.raises(SystemExit) as excinfo:
        DriftBrake.run_from_env()
    assert excinfo.value.code == 5


# from_env


def test_from_env_raises_when_no_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    with pytest.raises(MissingDatabaseURL):
        DriftBrake.from_env()


def test_from_env_reads_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/testdb")
    db = DriftBrake.from_env(interactive=False)
    assert db.database_url == "postgresql://user:pass@localhost/testdb"
