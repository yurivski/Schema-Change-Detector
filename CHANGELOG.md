<div align="center">

# Changelog

</div>

<br>

## [0.2.0]

### Adicionado

**Pacote Python instalável**
- Estrutura `src/driftbrake/` com todos os módulos do pacote.
- `pyproject.toml` com dependências declaradas, metadados do projeto e ponto de entrada `driftbrake`.
- Comando `pip install -e .` funcional.

**CLI com Typer (`driftbrake`)**
- Comando `init`: conecta no banco e gera `schema.lock.json` (contrato versionável).
- Comando `check`: compara o banco ao vivo contra o contrato e retorna exit code determinístico.
- Comando `diff`: compara dois arquivos JSON ou um arquivo contra o banco.
- Comando `snapshot`: captura o schema atual sem comparar (substitui `exportador.py` manual).
- Comando `update-contract`: atualiza o contrato após aprovar mudanças, com confirmação obrigatória.

**Leitura automática do PostgreSQL**
- `PostgresSchemaReader` usando SQLAlchemy Inspector.
- Captura: colunas, tipos, nullable, defaults, posição ordinal, primary keys, foreign keys, unique constraints, check constraints e indexes.
- Suporte a múltiplos schemas (`--schemas public,raw,analytics`).
- Aceita `DATABASE_URL` ou variáveis individuais `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

**Contrato versionado (`schema.lock.json`)**
- Formato estável com versão, timestamp, tipo de banco e schemas aninhados.
- Adequado para versionamento no Git.
- `ContractWriter` e `ContractLoader` para leitura e escrita consistentes.

**Modelos internos padronizados**
- `ColumnSchema`, `TableSchema`, `DatabaseSchema`, `SchemaChange`, `DiffResult`.
- Enums `Severity` (`BREAKING`, `WARNING`, `SAFE`) e `ChangeType` (15 tipos de mudança).

**Comparador independente de origem**
- `SchemaComparator` recebe dois objetos `DatabaseSchema` sem saber se vieram do banco ou de um arquivo.
- Detecta: tabelas adicionadas/removidas, colunas adicionadas/removidas, tipo alterado, nullable alterado, default alterado, primary key alterada, unique alterada, foreign key adicionada/alterada, posição ordinal alterada.
- Detecção de possível rename: quando uma coluna é removida e outra adicionada com tipo compatível na mesma tabela, sugere rename como `WARNING`.

**Classificador de impacto**
- `ImpactClassifier` com regras configuráveis por arquivo YAML.
- Regras sobrescrevíveis individualmente em `driftbrake.yml`.

**Matriz inteligente de compatibilidade de tipos**
- `type_compatibility.py` com lógica para `VARCHAR(n)`, `NUMERIC(p,s)`, inteiros, datas e tipos genéricos.
- Distingue alargamento (SAFE/WARNING) de estreitamento (BREAKING) de tamanho e precisão.

**Relatórios**
- Terminal com Rich: agrupado por severidade e tabela, com cores e resumo final.
- JSON estável (`schema_diff.json`) com status, resumo e lista de mudanças com before/after.
- HTML usando os templates existentes em `templates/` via Jinja2.
- Markdown para uso em comentários automáticos de pull requests.

**`SchemaGuard` — API de alto nível**
- `SchemaGuard(database_url, contract_path, ...)` para uso direto em pipelines Python.
- `SchemaGuard.from_env(contract_path)` para leitura automática de variáveis de ambiente.
- `check()` retorna `DiffResult` sem efeitos colaterais.
- `assert_compatible()` bloqueia o processo com exit code correto se houver mudanças proibidas.
- `save_reports()` e `print_report()` para controle granular de saída.

**Arquivo de configuração YAML**
- `driftbrake.yml` com suporte a `fail_on`, `warn_on`, filtro de schemas, tabelas e colunas ignoradas e override de regras.
- `driftbrake.example.yml` incluído no repositório como referência.

**Exit codes profissionais**
- `0` compatível, `1` warning strict, `2` breaking, `3` conexão, `4` contrato, `5` configuração, `6` interno.

**Testes automatizados**
- 57 testes unitários em `tests/unit/` cobrindo comparador, classificador e matriz de tipos.
- Fixtures em `tests/fixtures/` para testes sem dependência de banco.

**Exemplos**
- `examples/simple_pipeline/pipeline.py`: pipeline Python com `SchemaGuard.from_env()`.
- `examples/airflow/schema_check_dag.py`: DAG Airflow com `schema_check >> extract >> transform >> load`.
- `examples/dbt/check_before_run.sh`: execução de `driftbrake check` antes do `dbt run`.
- `examples/github_actions/schema-check.yml`: workflow de CI para validação em pull requests.

**CI do projeto**
- `.github/workflows/tests.yml`: lint, typecheck e testes em todo push e pull request.

**Makefile**
- Comandos: `install`, `test`, `lint`, `format`, `typecheck`, `check`.

### Alterado

- O JSON deixou de ser uma etapa obrigatória e passou a ser saída opcional do processo.
- A lógica de comparação foi desacoplada da leitura de arquivos: o comparador recebe objetos Python, não caminhos.
- O HTML report passou a usar Jinja2 em vez de substituição manual de strings.

### Deprecated

- `fonte/exportador.py`: substituído por `readers/postgres.py` e pelo comando `snapshot`.
- `fonte/comparador.py`: substituído por `comparators/schema_comparator.py` e pelo comando `check`.
- `fonte/relatorio.py`: substituído por `reporters/html_report.py`.
- `fonte/__init__.py`: sem função no novo pacote.
- `arquivos.py`: script de scaffolding da estrutura original, sem utilidade na versão atual.
- `requirements.txt`: substituído pelo `pyproject.toml`.

</div>
---

## [0.1.0]

### Adicionado

**Exportação de metadados**
- `fonte/exportador.py`: conecta no PostgreSQL via SQLAlchemy e extrai metadados de tabelas especificadas manualmente.
- Extrai: colunas, tipos, nullable, defaults, primary keys, foreign keys, unique constraints, check constraints e indexes.
- Salva snapshots JSON em `historico/` com sufixo de timestamp ou nome customizado.

**Comparação de snapshots**
- `fonte/comparador.py`: lê dois arquivos JSON e detecta colunas adicionadas, removidas e propriedades modificadas.
- Detecta mudanças em: tipo, nullable (not_null), default, primary key, unique e foreign key.
- Exibe resultado no terminal com classificação inline por mudança.

**Classificação de impacto (inline)**
- `BREAKING`: coluna removida, tipo alterado, NOT NULL adicionado, primary key mudou, foreign key mudou.
- `WARNING`: NOT NULL removido, foreign key adicionada, unique constraint mudou.
- `SAFE`: coluna nullable adicionada.

**Relatório HTML consolidado**
- `fonte/relatorio.py`: gera relatório HTML de todas as tabelas comparadas em um único arquivo.
- Usa templates em `templates/` (`base.html`, `tabela.html`, `secao_breaking.html`, `secao_warning.html`, `secao_safe.html`).
- Relatório salvo em `relatorios/relatorio_consolidado_YYYY-MM-DD_HH-MM-SS.html`.

**Templates HTML**
- Layout responsivo com CSS inline.
- Cards de resumo por severidade (breaking/warning/safe).
- Seções por tabela com badges coloridos.

**Configuração por variáveis de ambiente**
- `.env` com `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- Carregado via `python-dotenv`.

**Estrutura inicial do projeto**
- `arquivos.py`: script de scaffolding para criação automática de pastas e arquivos.
- `requirements.txt`: dependências do projeto (`sqlalchemy`, `psycopg2`, `pandas`, `dotenv`).

### Limitações conhecidas

- Fluxo manual: `exportador.py` → JSON → `comparador.py` → HTML.
- Tabelas a exportar definidas por lista hardcoded no `if __name__ == "__main__"`.
- Assume schema `public` em todas as operações.
- Não detecta reordenação de colunas.
- Não há testes automatizados.
- Não há CLI instalável.

---

[0.2.0]: https://github.com/yurivski/DriftBrake/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yurivski/DriftBrake/releases/tag/v0.1.0
