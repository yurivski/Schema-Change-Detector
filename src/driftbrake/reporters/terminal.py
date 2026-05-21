# Reporter de terminal usando Rich pra saída colorida e estruturada.

from __future__ import annotations

from driftbrake.models import DiffResult, SchemaChange, Severity


def _severity_style(severity: Severity) -> str:
    return {
        Severity.BREAKING: "bold red",
        Severity.WARNING: "bold yellow",
        Severity.SAFE: "bold green",
    }.get(severity, "white")


def _severity_label(severity: Severity) -> str:
    return {
        Severity.BREAKING: "[bold red]BREAKING[/bold red]",
        Severity.WARNING: "[bold yellow]WARNING[/bold yellow]",
        Severity.SAFE: "[bold green]SAFE[/bold green]",
    }.get(severity, severity.value)


class TerminalReporter:
    # Imprime um relatório de diff colorido e estruturado no terminal.

    def __init__(self, show_safe: bool = True) -> None:
        self.show_safe = show_safe

    def print(self, result: DiffResult) -> None:
        # Imprime o DiffResult no terminal usando Rich.
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            from rich import box
        except ImportError:
            self._print_plain(result)
            return

        console = Console()

        console.print()
        console.print(
            Panel(
                f"[bold]DriftBrake[/bold] — Comparison Report\n"
                f"Compared at: [dim]{result.compared_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n"
                f"Expected: [cyan]{result.expected_source}[/cyan]  "
                f"Current: [cyan]{result.current_source}[/cyan]",
                style="bold white on dark_blue",
                expand=False,
            )
        )

        # Resumo
        summary_table = Table(box=box.ROUNDED, show_header=False, expand=False)
        summary_table.add_column("Metric", style="bold")
        summary_table.add_column("Value")
        summary_table.add_row("Breaking Changes", f"[bold red]{result.total_breaking}[/bold red]")
        summary_table.add_row("Warnings", f"[bold yellow]{result.total_warnings}[/bold yellow]")
        summary_table.add_row("Safe Changes", f"[bold green]{result.total_safe}[/bold green]")
        summary_table.add_row("Total Changes", str(len(result.changes)))
        compatible_label = (
            "[bold green]Yes[/bold green]"
            if result.is_compatible
            else "[bold red]No[/bold red]"
        )
        summary_table.add_row("Compatible", compatible_label)
        console.print(summary_table)
        console.print()

        if not result.changes:
            console.print("[bold green]No schema changes detected.[/bold green]")
            return

        # Agrupa por tabela
        changes_by_table = result.changes_by_table()

        for table_key, changes in changes_by_table.items():
            breaking = [c for c in changes if c.severity == Severity.BREAKING]
            warnings = [c for c in changes if c.severity == Severity.WARNING]
            safe = [c for c in changes if c.severity == Severity.SAFE]

            header_parts = []
            if breaking:
                header_parts.append(f"[red]{len(breaking)} breaking[/red]")
            if warnings:
                header_parts.append(f"[yellow]{len(warnings)} warning[/yellow]")
            if safe:
                header_parts.append(f"[green]{len(safe)} safe[/green]")

            console.print(
                Panel(
                    f"[bold]{table_key}[/bold]  " + "  ".join(header_parts),
                    style="dim",
                    expand=False,
                )
            )

            grouped: list[tuple[str, list[SchemaChange]]] = []
            if breaking:
                grouped.append(("BREAKING", breaking))
            if warnings:
                grouped.append(("WARNING", warnings))
            if self.show_safe and safe:
                grouped.append(("SAFE", safe))

            for label, group in grouped:
                sev = Severity(label)
                tbl = Table(
                    title=f"{_severity_label(sev)} ({len(group)})",
                    box=box.SIMPLE_HEAVY,
                    show_header=True,
                    header_style="bold",
                    expand=True,
                )
                tbl.add_column("Column", style="cyan", no_wrap=True)
                tbl.add_column("Change Type")
                tbl.add_column("Before")
                tbl.add_column("After")
                tbl.add_column("Description")

                for change in group:
                    tbl.add_row(
                        change.column_name or "—",
                        change.change_type.value,
                        str(change.old_value) if change.old_value is not None else "—",
                        str(change.new_value) if change.new_value is not None else "—",
                        change.description,
                    )
                console.print(tbl)

        if not result.is_compatible:
            console.print(
                Panel(
                    "[bold red]DRIFTBRAKE CHECK FAILED[/bold red]\n"
                    "Breaking changes detected. Check the report above.",
                    style="red",
                    expand=False,
                )
            )
        else:
            console.print(
                Panel(
                    "[bold green]DRIFTBRAKE CHECK PASSED[/bold green]\n"
                    "No breaking changes detected.",
                    style="green",
                    expand=False,
                )
            )

    def _print_plain(self, result: DiffResult) -> None:
        # Saída em texto simples como alternativa quando Rich não está disponível.
        print(f"\nSchema Comparison Report — {result.compared_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Breaking: {result.total_breaking}  Warnings: {result.total_warnings}  Safe: {result.total_safe}")
        print()
        for change in result.changes:
            print(
                f"[{change.severity.value}] {change.schema_name}.{change.table_name}"
                f" | col={change.column_name or '-'} | {change.change_type.value}"
                f" | {change.old_value} -> {change.new_value}"
            )
        print()
        if result.is_compatible:
            print("DRIFTBRAKE CHECK PASSED")
        else:
            print("DRIFTBRAKE CHECK FAILED — Breaking changes detected.")
