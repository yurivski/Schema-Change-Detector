<div align="center">

# Changelog

</div>

Todas as mudanças significativas neste projeto são documentadas neste arquivo.

<br>

## [0.0.2] — 2026-05-22

### Adicionado

- **`driftbrake --version`:** exibe a versão instalada e encerra. Exemplo:
  ```
  DriftBrake 0.0.2
  ```
- **`driftbrake --info`:** exibe informações completas do ambiente e encerra. Exemplo:
  ```
  DriftBrake 0.0.2
  Python 3.13.5
  Platform Linux-6.5.0-parrot
  SQLAlchemy 2.0.49
  ```
- **pre-commit:** cada `git commit` roda o ruff automaticamente. Se tiver erro de lint, o commit é bloqueado até tu corrigir.
- **Separadores visuais no resumo:** a tabela de resumo no terminal agora exibe separadores entre as linhas (`show_lines=True`), tornando a leitura mais clara.
- **Colapso quando não há mudanças:** quando a comparação retorna 0 alterações, o output colapsa para uma linha única: `Schemas compatible — 0 changes detected.`

### Alterado

- **Idioma da CLI:** todas as legendas, descrições e mensagens dos comandos da CLI foram traduzidas para inglês. Comentários internos do código permanecem em português (Brasil).

### Corrigido

- **`load_dotenv()` não chamado automaticamente:** a CLI agora chama `load_dotenv()` antes de qualquer leitura de variável de ambiente, garantindo que arquivos `.env` no diretório atual sejam carregados automaticamente. Comportamento anterior exigia `source .env` manual no shell.
- **`driftbrake_version` desatualizada nos contratos:** o campo `driftbrake_version` no `schema.lock.json` agora é lido dinamicamente via `importlib.metadata.version()`, eliminando a versão hardcoded `"0.2.0"` que era gerada independente da versão instalada.
- **Mensagem "DRIFTBRAKE CHECK FAILED" no output do `diff`:** o comando `diff` é exploratório e sempre retorna exit code 0. A mensagem final agora exibe "DIFFERENCES DETECTED" (em amarelo) em vez de "DRIFTBRAKE CHECK FAILED" (em vermelho), eliminando a confusão entre falha real e resultado informativo.
- **Templates HTML fora do pacote (não incluídos na wheel):** a pasta `templates/` foi movida para dentro de `src/driftbrake/templates/`. O `html_report.py` agora carrega os templates via `PackageLoader("driftbrake", "templates")`, garantindo funcionamento tanto em editable install quanto em wheel publicada. O `pyproject.toml` foi atualizado com `include` para `.html`.

---

## [0.0.1] — 2026-05-21

Versão inicial publicada para travar o nome `driftbrake` no PyPI.

### Adicionado

**Pacote Python**

- Estrutura `src/driftbrake/` com todos os módulos do pacote.
- `pyproject.toml` com dependências declaradas, metadados do projeto e ponto de entrada `driftbrake`.
- Comando `pip install -e .` funcional.
- Suporte ao Python 3.10+ (substitui `StrEnum` por `str + Enum`).
- Configuração de exclusões de build no hatchling.
- `[project.urls]` e classifiers completos adicionados ao `pyproject.toml`.
- README traduzido para inglês.

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

**`SchemaGuard` — API**

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

**CI do projeto**

- `.github/workflows/ci.yml`: lint, typecheck e testes em todo push e pull request.

**Makefile**

- Comandos: `install`, `test`, `lint`, `format`, `typecheck`, `check`.

### Alterado

- O JSON deixou de ser uma etapa obrigatória e passou a ser saída opcional do processo.
- A lógica de comparação foi desacoplada da leitura de arquivos: o comparador recebe objetos Python, não caminhos.
- O HTML report passou a usar Jinja2 em vez de substituição manual de strings.
- Dependências refatoradas: `psycopg2` movido para extras `[postgres]`.

### Descontinuado

- `fonte/exportador.py`: substituído por `readers/postgres.py` e pelo comando `snapshot`.
- `fonte/comparador.py`: substituído por `comparators/schema_comparator.py` e pelo comando `check`.
- `fonte/relatorio.py`: substituído por `reporters/html_report.py`.
- `fonte/__init__.py`: sem função no novo pacote.
- `arquivos.py`: script de scaffolding da estrutura original, sem utilidade na versão atual.
- `requirements.txt`: substituído pelo `pyproject.toml`.

---

[0.0.2]: https://github.com/yurivski/DriftBrake/releases/tag/v0.0.2
[0.0.1]: https://github.com/yurivski/DriftBrake/releases/tag/v0.0.1