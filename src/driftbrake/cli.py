"""
CLI do DriftBrake usando Typer.

Comandos:
    init            - Inicializa um novo contrato de schema a partir de um banco de dados ativo.
    check           - Compara o banco de dados ativo contra um contrato.
    diff            - Compara dois arquivos de schema ou um arquivo contra um banco de dados.
    snapshot        - Captura o schema atual sem realizar comparação.
    update-contract - Atualiza o contrato para refletir o estado atual do banco de dados.

Códigos de saída:
    0 - Schema compatível / sucesso.
    1 - Aviso em modo estrito.
    2 - Alteração crítica detectada.
    3 - Erro de conexão com o banco de dados.
    4 - Contrato ausente ou inválido.
    5 - Erro de configuração.
    6 - Erro interno.
"""

from __future__ import annotations

import os
import platform
import sys
from importlib.metadata import version as get_version
from typing import Annotated

import typer
from dotenv import load_dotenv

from driftbrake.comparators.schema_comparator import SchemaComparator
from driftbrake.contracts.writer import ContractWriter
from driftbrake.exceptions import SchemaConnectionError, SchemaContractNotFoundError
from driftbrake.guard import SchemaGuard
from driftbrake.models import Severity
from driftbrake.readers.json_reader import JsonSchemaReader
from driftbrake.readers.postgres import PostgresSchemaReader
from driftbrake.reporters.html_report import HtmlReporter
from driftbrake.reporters.json_report import JsonReporter
from driftbrake.reporters.terminal import TerminalReporter

app = typer.Typer(
    name="driftbrake",
    help="DriftBrake — Validate schema contracts before running data pipelines.",
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    # Exibe a versão e encerra o processo.
    if value:
        v = get_version("driftbrake")
        typer.echo(f"DriftBrake {v}")
        raise typer.Exit()


def _info_callback(value: bool) -> None:
    # Exibe informações detalhadas sobre o ambiente e encerra o processo.
    if value:
        import sqlalchemy

        v = get_version("driftbrake")
        typer.echo(f"DriftBrake {v}")
        typer.echo(f"Python {sys.version.split()[0]}")
        typer.echo(f"Platform {platform.platform()}")
        typer.echo(f"SQLAlchemy {sqlalchemy.__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    info: bool = typer.Option(
        False,
        "--info",
        callback=_info_callback,
        is_eager=True,
        help="Show environment info (version, Python, platform, SQLAlchemy) and exit.",
    ),
) -> None:
    pass


def _build_db_url(db_url: str | None) -> str:
    # Resolve a URL do banco de dados a partir do argumento ou variáveis de ambiente.
    load_dotenv()

    if db_url:
        return db_url
    if database_url := os.getenv("DATABASE_URL"):
        return database_url
    if not os.getenv("DB_NAME") or not os.getenv("DB_USER"):
        typer.echo(
            "[ERROR] Database URL not provided. "
            "Set --db-url or the DATABASE_URL environment variable.",
            err=True,
        )
        raise typer.Exit(3)
    return (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
        f"/{os.getenv('DB_NAME')}"
    )


@app.command("init", help="Initialize a schema contract by connecting to the database.")
def init(
    db_url: Annotated[
        str | None,
        typer.Option("--db-url", help="Database connection URL."),
    ] = None,
    schemas: Annotated[
        str,
        typer.Option("--schemas", help="Comma-separated list of schemas to capture."),
    ] = "public",
    output: Annotated[
        str,
        typer.Option("--output", help="Output path for the schema contract file."),
    ] = "schema.lock.json",
) -> None:
    # Inicializa um novo contrato de schema a partir de um banco de dados ativo.

    url = _build_db_url(db_url)
    schema_list = [s.strip() for s in schemas.split(",") if s.strip()]

    typer.echo(f"Connecting to database and reading schema ({', '.join(schema_list)})...")
    try:
        reader = PostgresSchemaReader(database_url=url, schemas=schema_list)
        db_schema = reader.read()
    except SchemaConnectionError as exc:
        typer.echo(f"[ERROR] Connection failed: {exc}", err=True)
        raise typer.Exit(3)

    writer = ContractWriter(output)
    writer.write(db_schema)
    typer.echo(f"[OK] Schema contract saved to: {output}")

    total_tables = sum(len(tables) for tables in db_schema.schemas.values())
    typer.echo(f"     {total_tables} table(s) captured across {len(db_schema.schemas)} schema(s).")


@app.command(
    "check",
    help="Check for divergences between the live database and the schema contract.",
)
def check(
    db_url: Annotated[
        str | None,
        typer.Option("--db-url", help="Database connection URL."),
    ] = None,
    contract: Annotated[
        str,
        typer.Option("--contract", help="Path to the schema.lock.json contract file."),
    ] = "schema.lock.json",
    fail_on: Annotated[
        str,
        typer.Option("--fail-on", help="Severity levels (comma-sep.) that cause a non-zero exit."),
    ] = "BREAKING",
    json_output: Annotated[
        str | None,
        typer.Option("--json", help="Write the diff report as JSON to this path."),
    ] = None,
    html_output: Annotated[
        str | None,
        typer.Option("--html", help="Write the diff report as HTML to this path."),
    ] = None,
    markdown_output: Annotated[
        str | None,
        typer.Option("--markdown", help="Write the diff report as Markdown to this path."),
    ] = None,
    config: Annotated[
        str | None,
        typer.Option("--config", help="Path to the driftbrake.yml configuration file."),
    ] = None,
) -> None:
    # Compara o schema do banco de dados ativo contra um arquivo de contrato.
    url = _build_db_url(db_url)
    fail_on_list = [s.strip() for s in fail_on.split(",") if s.strip()]

    try:
        guard = SchemaGuard(
            database_url=url,
            contract_path=contract,
            config_path=config,
            output_json=json_output,
            output_html=html_output,
            output_markdown=markdown_output,
            fail_on=fail_on_list,
        )
        result = guard.check()
    except SchemaConnectionError as exc:
        typer.echo(f"[ERROR] Connection failed: {exc}", err=True)
        raise typer.Exit(3)
    except SchemaContractNotFoundError as exc:
        typer.echo(f"[ERROR] Contract error: {exc}", err=True)
        raise typer.Exit(4)
    except Exception as exc:
        typer.echo(f"[ERROR] Unexpected error: {exc}", err=True)
        raise typer.Exit(6)

    guard.save_reports(result)
    guard.print_report(result)

    fail_severities = [Severity(s.upper()) for s in fail_on_list]
    failing = [c for c in result.changes if c.severity in fail_severities]
    if failing:
        typer.echo(
            f"\n[FAILED] {len(failing)} change(s) above threshold ({fail_on}). "
            "Exiting with code 2.",
            err=True,
        )
        raise typer.Exit(2)

    typer.echo("\n[OK] Schema is compatible.")


@app.command("diff", help="Compare two schemas (JSON files or database) and show differences.")
def diff(
    old: Annotated[
        str | None,
        typer.Option("--old", help="Path to the JSON file representing the expected (old) schema."),
    ] = None,
    new: Annotated[
        str | None,
        typer.Option("--new", help="Path to the JSON file representing the current (new) schema."),
    ] = None,
    new_db: Annotated[
        str | None,
        typer.Option("--new-db", help="Database URL to use as the current (new) schema."),
    ] = None,
    json_output: Annotated[
        str | None,
        typer.Option("--json", help="Write the diff report as JSON to this path."),
    ] = None,
    html_output: Annotated[
        str | None,
        typer.Option("--html", help="Write the diff report as HTML to this path."),
    ] = None,
) -> None:
    # Compara duas fontes de schema (arquivos ou um arquivo contra um banco de dados ativo).

    if not old:
        typer.echo("[ERROR] --old is required.", err=True)
        raise typer.Exit(6)

    try:
        expected = JsonSchemaReader(old).read()
    except SchemaContractNotFoundError as exc:
        typer.echo(f"[ERROR] {exc}", err=True)
        raise typer.Exit(4)

    current_source = ""
    try:
        if new_db:
            current = PostgresSchemaReader(database_url=new_db).read()
            current_source = new_db
        elif new:
            current = JsonSchemaReader(new).read()
            current_source = new
        else:
            typer.echo("[ERROR] Provide --new or --new-db.", err=True)
            raise typer.Exit(6)
    except SchemaConnectionError as exc:
        typer.echo(f"[ERROR] {exc}", err=True)
        raise typer.Exit(3)
    except SchemaContractNotFoundError as exc:
        typer.echo(f"[ERROR] {exc}", err=True)
        raise typer.Exit(4)

    comparator = SchemaComparator()
    result = comparator.compare(
        expected=expected,
        current=current,
        expected_source=old,
        current_source=current_source,
    )

    TerminalReporter(mode="diff").print(result)

    if json_output:
        JsonReporter(json_output).write(result)
        typer.echo(f"JSON report: {json_output}")
    if html_output:
        try:
            HtmlReporter(html_output).write(result)
            typer.echo(f"HTML report: {html_output}")
        except FileNotFoundError as exc:
            typer.echo(f"[WARNING] HTML report skipped: {exc}", err=True)


@app.command("snapshot", help="Capture the current database schema without comparing.")
def snapshot(
    db_url: Annotated[
        str | None,
        typer.Option("--db-url", help="Database connection URL."),
    ] = None,
    output: Annotated[
        str,
        typer.Option("--output", help="Output path for the snapshot JSON file."),
    ] = "schema.snapshot.json",
    schemas: Annotated[
        str,
        typer.Option("--schemas", help="Comma-separated list of schemas to capture."),
    ] = "public",
) -> None:
    """Captures a snapshot of the current database schema without comparing."""
    url = _build_db_url(db_url)
    schema_list = [s.strip() for s in schemas.split(",") if s.strip()]

    typer.echo(f"Capturing schema snapshot from {url.split('@')[-1]}...")
    try:
        reader = PostgresSchemaReader(database_url=url, schemas=schema_list)
        db_schema = reader.read()
    except SchemaConnectionError as exc:
        typer.echo(f"[ERROR] {exc}", err=True)
        raise typer.Exit(3)

    ContractWriter(output).write(db_schema)
    total_tables = sum(len(t) for t in db_schema.schemas.values())
    typer.echo(f"[OK] Snapshot saved to {output} ({total_tables} tables).")


@app.command("update-contract", help="Update the schema contract to match the current database.")
def update_contract(
    db_url: Annotated[
        str | None,
        typer.Option("--db-url", help="Database connection URL."),
    ] = None,
    contract: Annotated[
        str,
        typer.Option("--contract", help="Path to the schema.lock.json to be updated."),
    ] = "schema.lock.json",
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt."),
    ] = False,
    schemas: Annotated[
        str,
        typer.Option("--schemas", help="Comma-separated list of schemas to capture."),
    ] = "public",
) -> None:
    """Updates the schema contract to reflect the current state of the database."""
    url = _build_db_url(db_url)
    schema_list = [s.strip() for s in schemas.split(",") if s.strip()]

    if not yes:
        confirmed = typer.confirm(
            f"This will overwrite '{contract}' with the current database schema. Continue?"
        )
        if not confirmed:
            typer.echo("Operation cancelled.")
            raise typer.Exit(0)

    typer.echo("Reading current database schema...")
    try:
        reader = PostgresSchemaReader(database_url=url, schemas=schema_list)
        db_schema = reader.read()
    except SchemaConnectionError as exc:
        typer.echo(f"[ERROR] {exc}", err=True)
        raise typer.Exit(3)

    ContractWriter(contract).write(db_schema)
    total_tables = sum(len(t) for t in db_schema.schemas.values())
    typer.echo(f"[OK] Contract updated: {contract} ({total_tables} tables).")


if __name__ == "__main__":
    app()
