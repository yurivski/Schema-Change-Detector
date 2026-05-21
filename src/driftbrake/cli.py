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

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from driftbrake.contracts.writer import ContractWriter
from driftbrake.exceptions import SchemaConnectionError
from driftbrake.readers.postgres import PostgresSchemaReader

from driftbrake.comparators.schema_comparator import SchemaComparator
from driftbrake.exceptions import SchemaConnectionError, SchemaContractNotFoundError
from driftbrake.readers.json_reader import JsonSchemaReader
from driftbrake.readers.postgres import PostgresSchemaReader
from driftbrake.reporters.html_report import HtmlReporter
from driftbrake.reporters.json_report import JsonReporter
from driftbrake.reporters.terminal import TerminalReporter

from driftbrake.exceptions import SchemaConnectionError, SchemaContractNotFoundError
from driftbrake.guard import SchemaGuard

from driftbrake.models import Severity

from driftbrake.contracts.writer import ContractWriter
from driftbrake.exceptions import SchemaConnectionError
from driftbrake.readers.postgres import PostgresSchemaReader

from driftbrake.contracts.writer import ContractWriter
from driftbrake.exceptions import SchemaConnectionError
from driftbrake.readers.postgres import PostgresSchemaReader

app = typer.Typer(
    name="driftbrake",
    help="DriftBrake — Valide contratos de schema antes de executar pipelines de dados.",
    add_completion=False,
)


def _build_db_url(db_url: str | None) -> str:
    # Resolve a URL do banco de dados a partir do argumento ou variáveis de ambiente.
    import os

    if db_url:
        return db_url
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "")
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    if not name or not user:
        typer.echo(
            "[ERRO] URL do banco de dados não informada. Defina --db-url ou a variável DATABASE_URL.",
            err=True,
        )
        raise typer.Exit(3)
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


@app.command("init")
def init(
    db_url: Annotated[
        Optional[str],
        typer.Option("--db-url", help="URL de conexão com o banco de dados."),
    ] = None,
    schemas: Annotated[
        str,
        typer.Option("--schemas", help="Lista de schemas separados por vírgula."),
    ] = "public",
    output: Annotated[
        str,
        typer.Option("--output", help="Caminho de saída para o arquivo de contrato de schema."),
    ] = "schema.lock.json",
) -> None:
    # Inicializa um novo contrato de schema a partir de um banco de dados ativo.

    url = _build_db_url(db_url)
    schema_list = [s.strip() for s in schemas.split(",") if s.strip()]

    typer.echo(f"Conectando ao banco de dados e lendo o schema ({', '.join(schema_list)})...")
    try:
        reader = PostgresSchemaReader(database_url=url, schemas=schema_list)
        db_schema = reader.read()
    except SchemaConnectionError as exc:
        typer.echo(f"[ERRO] Falha na conexão: {exc}", err=True)
        raise typer.Exit(3)

    writer = ContractWriter(output)
    writer.write(db_schema)
    typer.echo(f"[OK] Contrato de schema salvo em: {output}")

    total_tables = sum(len(tables) for tables in db_schema.schemas.values())
    typer.echo(f"     {total_tables} tabela(s) capturada(s) em {len(db_schema.schemas)} schema(s).")


@app.command("check")
def check(
    db_url: Annotated[
        Optional[str],
        typer.Option("--db-url", help="URL de conexão com o banco de dados."),
    ] = None,
    contract: Annotated[
        str,
        typer.Option("--contract", help="Caminho para o arquivo de contrato schema.lock.json."),
    ] = "schema.lock.json",
    fail_on: Annotated[
        str,
        typer.Option("--fail-on", help="Níveis de severidade separados por vírgula que causam falha."),
    ] = "BREAKING",
    json_output: Annotated[
        Optional[str],
        typer.Option("--json", help="Grava o relatório de diff em JSON neste caminho."),
    ] = None,
    html_output: Annotated[
        Optional[str],
        typer.Option("--html", help="Grava o relatório de diff em HTML neste caminho."),
    ] = None,
    markdown_output: Annotated[
        Optional[str],
        typer.Option("--markdown", help="Grava o relatório de diff em Markdown neste caminho."),
    ] = None,
    config: Annotated[
        Optional[str],
        typer.Option("--config", help="Caminho para o arquivo de configuração driftbrake.yml."),
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
        typer.echo(f"[ERRO] Falha na conexão: {exc}", err=True)
        raise typer.Exit(3)
    except SchemaContractNotFoundError as exc:
        typer.echo(f"[ERRO] Erro no contrato: {exc}", err=True)
        raise typer.Exit(4)
    except Exception as exc:
        typer.echo(f"[ERRO] Erro inesperado: {exc}", err=True)
        raise typer.Exit(6)

    guard.save_reports(result)
    guard.print_report(result)

    fail_severities = [Severity(s.upper()) for s in fail_on_list]
    failing = [c for c in result.changes if c.severity in fail_severities]
    if failing:
        typer.echo(
            f"\n[FALHA] {len(failing)} alteração(ões) acima do limiar ({fail_on}). Saindo com código 2.",
            err=True,
        )
        raise typer.Exit(2)

    typer.echo("\n[OK] Schema compatível.")


@app.command("diff")
def diff(
    old: Annotated[
        Optional[str],
        typer.Option("--old", help="Caminho para o arquivo JSON do schema antigo."),
    ] = None,
    new: Annotated[
        Optional[str],
        typer.Option("--new", help="Caminho para o arquivo JSON do schema novo."),
    ] = None,
    new_db: Annotated[
        Optional[str],
        typer.Option("--new-db", help="URL do banco de dados a ser usado como schema 'novo'."),
    ] = None,
    json_output: Annotated[
        Optional[str],
        typer.Option("--json", help="Grava o relatório de diff em JSON neste caminho."),
    ] = None,
    html_output: Annotated[
        Optional[str],
        typer.Option("--html", help="Grava o relatório de diff em HTML neste caminho."),
    ] = None,
) -> None:
    # Compara duas fontes de schema (arquivos ou um arquivo contra um banco de dados ativo).

    if not old:
        typer.echo("[ERRO] --old é obrigatório.", err=True)
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
            typer.echo("[ERRO] Informe --new ou --new-db.", err=True)
            raise typer.Exit(6)
    except SchemaConnectionError as exc:
        typer.echo(f"[ERRO] {exc}", err=True)
        raise typer.Exit(3)
    except SchemaContractNotFoundError as exc:
        typer.echo(f"[ERRO] {exc}", err=True)
        raise typer.Exit(4)

    comparator = SchemaComparator()
    result = comparator.compare(
        expected=expected,
        current=current,
        expected_source=old,
        current_source=current_source,
    )

    TerminalReporter().print(result)

    if json_output:
        JsonReporter(json_output).write(result)
        typer.echo(f"Relatório JSON: {json_output}")
    if html_output:
        try:
            HtmlReporter(html_output).write(result)
            typer.echo(f"Relatório HTML: {html_output}")
        except FileNotFoundError as exc:
            typer.echo(f"[AVISO] Relatório HTML ignorado: {exc}", err=True)


@app.command("snapshot")
def snapshot(
    db_url: Annotated[
        Optional[str],
        typer.Option("--db-url", help="URL de conexão com o banco de dados."),
    ] = None,
    output: Annotated[
        str,
        typer.Option("--output", help="Caminho de saída para o arquivo JSON de snapshot."),
    ] = "schema.snapshot.json",
    schemas: Annotated[
        str,
        typer.Option("--schemas", help="Lista de schemas separados por vírgula."),
    ] = "public",
) -> None:
    """Captura um snapshot do schema atual do banco de dados sem realizar comparação."""
    url = _build_db_url(db_url)
    schema_list = [s.strip() for s in schemas.split(",") if s.strip()]

    typer.echo(f"Capturando snapshot do schema de {url.split('@')[-1]}...")
    try:
        reader = PostgresSchemaReader(database_url=url, schemas=schema_list)
        db_schema = reader.read()
    except SchemaConnectionError as exc:
        typer.echo(f"[ERRO] {exc}", err=True)
        raise typer.Exit(3)

    ContractWriter(output).write(db_schema)
    total_tables = sum(len(t) for t in db_schema.schemas.values())
    typer.echo(f"[OK] Snapshot salvo em {output} ({total_tables} tabelas).")


@app.command("update-contract")
def update_contract(
    db_url: Annotated[
        Optional[str],
        typer.Option("--db-url", help="URL de conexão com o banco de dados."),
    ] = None,
    contract: Annotated[
        str,
        typer.Option("--contract", help="Caminho para o schema.lock.json a ser atualizado."),
    ] = "schema.lock.json",
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Pula a confirmação interativa."),
    ] = False,
    schemas: Annotated[
        str,
        typer.Option("--schemas", help="Lista de schemas separados por vírgula."),
    ] = "public",
) -> None:
    """Atualiza o contrato de schema para refletir o estado atual do banco de dados."""
    url = _build_db_url(db_url)
    schema_list = [s.strip() for s in schemas.split(",") if s.strip()]

    if not yes:
        confirmed = typer.confirm(
            f"Isso irá sobrescrever '{contract}' com o schema atual do banco de dados. Continuar?"
        )
        if not confirmed:
            typer.echo("Operação cancelada.")
            raise typer.Exit(0)

    typer.echo("Lendo o schema atual do banco de dados...")
    try:
        reader = PostgresSchemaReader(database_url=url, schemas=schema_list)
        db_schema = reader.read()
    except SchemaConnectionError as exc:
        typer.echo(f"[ERRO] {exc}", err=True)
        raise typer.Exit(3)

    ContractWriter(contract).write(db_schema)
    total_tables = sum(len(t) for t in db_schema.schemas.values())
    typer.echo(f"[OK] Contrato atualizado: {contract} ({total_tables} tabelas).")


if __name__ == "__main__":
    app()
