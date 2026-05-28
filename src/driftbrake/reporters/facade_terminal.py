# FacadeTerminalReporter — TerminalReporter que implementa o protocolo Reporter do DriftBrake.

from __future__ import annotations

import sys


class FacadeTerminalReporter:
    """Reporter padrão para DriftBrake. Imprime em stdout/stderr."""

    def __init__(self, verbose: bool = False, version: str = "0.1.0") -> None:
        self.verbose = verbose
        self.version = version

    def _header(self) -> None:
        print(f"DriftBrake {self.version}")

    def _change_lines(self, result, severity_attr: str) -> None:
        changes = getattr(result, severity_attr)
        for c in changes:
            col = f".{c.column_name}" if c.column_name else ""
            print(f"  - {c.schema_name}.{c.table_name}{col}: {c.description}")

    def on_no_drift(self, result) -> None:
        if self.verbose:
            self._header()
        print("[OK] DriftBrake: no schema drift detected.")

    def on_safe(self, result) -> None:
        if self.verbose:
            self._header()
        print(f"[INFO] DriftBrake: {result.safe_count} safe schema change(s) detected.")
        if self.verbose:
            self._change_lines(result, "safe_changes")

    def on_warning(self, result) -> None:
        if self.verbose:
            self._header()
        print(f"[WARN] DriftBrake: {result.warning_count} warning change(s) detected.")
        self._change_lines(result, "warnings")

    def on_breaking(self, result) -> None:
        if self.verbose:
            self._header()
        print(
            f"[BLOCKED] DriftBrake: {result.breaking_count} breaking change(s) detected.",
            file=sys.stderr,
        )
        self._change_lines(result, "breaking_changes")

    def on_contract_missing(self, contract_path: str) -> None:
        print(f"No schema contract found: {contract_path}")

    def on_contract_created(self, contract_path: str) -> None:
        if self.verbose:
            self._header()
        print(f"[OK] Contract created: {contract_path}")

    def on_released(self) -> None:
        print("[OK] Pipeline released.")

    def on_blocked(self, reason: str) -> None:
        print(f"[BLOCKED] {reason}", file=sys.stderr)
        print("Pipeline blocked.", file=sys.stderr)
