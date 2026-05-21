"""
Exemplo de DAG Airflow: schema_check >> extract >> transform >> load.

Este DAG executa uma verificação de compatibilidade de schema antes de cada
execução do pipeline. Se alterações críticas forem detectadas, o pipeline é
interrompido imediatamente.

Requisitos:
    pip install apache-airflow driftbrake
"""

import os

from airflow.exceptions import AirflowException
from driftbrake import SchemaGuard
from driftbrake.exceptions import BreakingSchemaChangeError
from driftbrake.models import Severity

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["data-alerts@yourcompany.com"],
}


def task_schema_check(**context) -> None:
    """
    Valida o schema do banco de dados contra o contrato versionado.
    Lança AirflowException se alterações críticas forem encontradas.
    """

    database_url = os.environ.get("DATABASE_URL") or (
        f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '5432')}/{os.environ['DB_NAME']}"
    )

    guard = SchemaGuard(
        database_url=database_url,
        contract_path="/opt/airflow/dags/schema.lock.json",
        fail_on=["BREAKING"],
        output_json=f"/opt/airflow/logs/schema_diff_{context['ds_nodash']}.json",
        output_html=f"/opt/airflow/logs/schema_diff_{context['ds_nodash']}.html",
    )

    result = guard.check()
    guard.save_reports(result)
    guard.print_report(result)

    if result.has_breaking:
        raise AirflowException(
            f"Schema check failed: {result.total_breaking} breaking change(s) detected. "
            "Pipeline halted. Review the schema diff report."
        )


def task_extract(**context) -> dict:
    """Extrai dados da fonte."""
    print(f"Extraindo dados para {context['ds']}...")
    # Substitua pela lógica de extração real
    return {"records": 0, "date": context["ds"]}


def task_transform(**context) -> None:
    """Transforma os dados extraídos."""
    print("Transformando dados...")
    # Substitua pela lógica de transformação real


def task_load(**context) -> None:
    """Carrega os dados transformados no destino."""
    print("Carregando dados no destino...")
    # Substitua pela lógica de carga real


with DAG(
    dag_id="schema_guarded_pipeline",
    description="Pipeline de dados com validação de contrato de schema",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["data-engineering", "schema-check"],
) as dag:
    schema_check = PythonOperator(
        task_id="schema_check",
        python_callable=task_schema_check,
    )

    extract = PythonOperator(
        task_id="extract",
        python_callable=task_extract,
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=task_transform,
    )

    load = PythonOperator(
        task_id="load",
        python_callable=task_load,
    )

    schema_check >> extract >> transform >> load
