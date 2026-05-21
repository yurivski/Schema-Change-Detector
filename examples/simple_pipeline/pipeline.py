"""
Exemplo de pipeline simples usando SchemaGuard.

Este script demonstra como integrar a verificação de contrato de schema
em um pipeline de dados antes de executar transformações.

Uso:
    DATABASE_URL=postgresql://user:pass@localhost/db python pipeline.py
"""

from driftbrake import SchemaGuard


def extract():
    print("[EXTRACT] Lendo dados da fonte...")
    # Insira sua lógica de extração aqui
    return {"records": 1000}


def transform(data: dict) -> dict:
    print(f"[TRANSFORM] Processando {data['records']} registros...")
    # Insira sua lógica de transformação aqui
    return {**data, "transformed": True}


def load(data: dict) -> None:
    print(f"[LOAD] Gravando {data['records']} registros no destino...")
    # Insira sua lógica de carga aqui
    print("[LOAD] Concluído.")


def run_pipeline() -> None:
    data = extract()
    data = transform(data)
    load(data)
    print("\nPipeline concluído com sucesso.")


def main() -> None:
    """
    Ponto de entrada. O schema é validado antes do pipeline executar.
    Encerra com código 2 se alterações críticas forem detectadas.
    """
    print("Validando contrato de schema...")
    SchemaGuard.from_env(
        contract_path="schema.lock.json",
        fail_on=["BREAKING"],
        output_json="reports/schema_diff.json",
        output_html="reports/schema_diff.html",
    ).assert_compatible()

    print("Schema compatível. Iniciando pipeline...\n")
    run_pipeline()


if __name__ == "__main__":
    main()
