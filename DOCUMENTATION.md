<div align="center">

# **DriftBrake** <br> Documentação

Bancos de dados mudam. Uma coluna é removida, um tipo é alterado, uma tabela é renomeada. Se isso acontece sem controle, pipelines de dados quebram em silêncio, e você só descobre horas depois, com dados corrompidos ou processamento parado. O **DriftBrake** resolve isso com um conceito simples: você cria um "contrato" que descreve exatamente como seu banco deve ser. Antes de executar qualquer pipeline, a ferramenta compara o banco real com esse contrato e avisa (ou bloqueia) se algo mudou.

**DriftBrake** é um projeto de pacote Python, que lê automaticamente o schema atual do banco de dados PostgreSQL, compara contra um contrato versionado (`schema.lock.json`), classifica mudanças por impacto e pode bloquear pipelines antes que eles quebrem em produção.

</div>

<br>

---

<div align="center">

**Atalho por categoria: clique no título sublinhado para expandir.**

</div>

<details>
<summary><b><code>INSTALAÇÃO</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

```bash
pip install -e .
```

Para instalar com dependências de desenvolvimento:

```bash
pip install -e ".[dev]"
pre-commit install
```

Verifique a instalação:

```bash
driftbrake --help
```

Verifique a versão instalada:

```bash
driftbrake --version
```

```
DriftBrake 0.0.2
```

---
</details>

<br>

<details>
<summary><b><code>Resumo por situação</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

| Situação | Comando |
|---|---|
| Primeira vez usando a ferramenta | `driftbrake init` |
| Verificar se o banco mudou antes de rodar o pipeline | `driftbrake check` |
| Comparar dois estados sem mexer no contrato | `driftbrake diff --old arquivo1.json --new arquivo2.json` |
| Guardar o estado atual do banco como referência futura | `driftbrake snapshot --output snapshots/nome.json` |
| Uma migration foi aplicada e as mudanças são intencionais | `driftbrake update-contract --yes` |
| Ver o relatório de mudanças em HTML | `driftbrake check --html relatorio.html` |


### Resumo dos comandos CLI

| Comando | Descrição |
|---|---|
| `driftbrake init` | Gera `schema.lock.json` a partir do banco atual |
| `driftbrake check` | Compara o banco contra o contrato e retorna exit code |
| `driftbrake diff` | Compara dois JSONs ou um JSON contra o banco |
| `driftbrake snapshot` | Captura o schema atual sem comparar |
| `driftbrake update-contract` | Atualiza o contrato para refletir o estado atual |

---
</details>

<br>

<details>
<summary><b><code>Config. do seu arquivo .env</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

As credenciais abaixo são exemplo de como devem estar no seu `.env`, são usadas automaticamente quando você não passa `--db-url`:

| Variável | Valor |
|---|---|
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/mydb` |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `mydb` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | `secrets` |

**Acesso ao banco de dados:** a ferramenta usa o SQLAlchemy por baixo dos panos. Quando você roda qualquer comando, ela monta a URL de conexão no formato `postgresql://usuario:senha@host:porta/banco` e usa o driver `psycopg2` para se conectar. O SQLAlchemy então usa o `Inspector`, uma API interna que consulta o catálogo do PostgreSQL (`information_schema` e `pg_catalog`) para ler metadados de tabelas, colunas, tipos, constraints e índices. Nenhuma linha dos seus dados é lida, apenas a estrutura.

**Prioridade da conexão:** se `DATABASE_URL` estiver definida no ambiente, ela tem prioridade total. Só se ela não existir, a ferramenta monta a URL juntando `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`.

---
</details>

<br>

<details>
<summary><b><code>Config. do arquivo YML</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

Crie um `driftbrake.yml` baseado no `driftbrake.example.yml`:

```yaml
fail_on:
  - BREAKING

tables:
  ignore:
    - alembic_version
    - flyway_schema_history

columns:
  ignore:
    orders:
      - updated_at
      [...]
```

Passe o arquivo para a CLI com `--config driftbrake.yml` ou para o `SchemaGuard` com `config_path="driftbrake.yml"`.

---
</details>


<br>

<details>
<summary><b><code>Conexão com o banco de dados</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

A ferramenta aceita a URL do banco de três formas, em ordem de prioridade:

**1. Argumento direto na CLI:**

```bash
driftbrake check --db-url "postgresql://user:pass@localhost:5432/mydb"
```

**2. Variável de ambiente `DATABASE_URL`:**

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
driftbrake check
```

**3. Variáveis individuais no `.env` ou no ambiente:**

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
DB_USER=postgres
DB_PASSWORD=secret
```

---
</details>

<br>

<details>
<summary><b><code>Comandos e exemplos de saídas</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

### 0. `--version` e `--info` — Verificar versão e ambiente

#### `driftbrake --version`

Exibe a versão instalada do DriftBrake e encerra.

```bash
driftbrake --version
```

```
DriftBrake 0.0.2
```

<br>

#### `driftbrake --info`

Exibe informações completas sobre o ambiente de execução e encerra. Útil para reportar problemas.

```bash
driftbrake --info
```

```
DriftBrake 0.0.2
Python 3.13.5
Platform Linux-6.5.0-parrot7-amd64
SQLAlchemy 2.0.49
```

<br>

---

### 1. `init` — Criar o contrato pela primeira vez

Conecta ao seu PostgreSQL, lê a estrutura completa do banco (tabelas, colunas, tipos, constraints, índices) e salva tudo em um arquivo JSON. Esse arquivo se torna o contrato, a "foto" do estado atual do banco.

**Primeira execução:** sem o contrato, não há nada para comparar. O `init` é sempre o ponto de partida. Você roda uma vez, commita o arquivo no git, e a partir daí qualquer mudança no banco pode ser detectada. O `init` vem antes de tudo porque ele *cria* o ponto de referência. Não faz sentido rodar `check` antes de ter um contrato. Execução:

#### `driftbrake init`

Conecta no banco, lê o schema atual e cria o contrato `schema.lock.json`. Esse arquivo deve ser versionado no Git.

```bash
driftbrake init \
  --db-url "$DATABASE_URL" \
  --schemas public \
  --output schema.lock.json
```

<br>

**Opções:**

| Opção | Padrão | O que faz |
|---|---|---|
| `--db-url` | lê do `.env` | URL completa de conexão com o PostgreSQL |
| `--schemas` | `public` | Quais schemas do PostgreSQL capturar. Separe por vírgula para mais de um |
| `--output` | `schema.lock.json` | Nome e caminho do arquivo de contrato gerado |

**Exit codes:** `0` sucesso, `3` erro de conexão.

<br>

```bash
# Forma mais simples, usa as variáveis do .env automaticamente
driftbrake init

# Especificando o banco explicitamente
driftbrake init --db-url "postgresql://user:pass@localhost:5432/mydb"

# Capturando schemas específicos (além do public)
driftbrake init --schemas "public,analytics,staging"

# Salvando o contrato em outro caminho
driftbrake init --output "contratos/schema_producao.lock.json"

# Tudo junto
driftbrake init \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --schemas "public" \
  --output "schema.lock.json"
```

<br>

**Exemplo de arquivo gerado:**
```json
{
  "contract_version": "1.0",
  "generated_by": "driftbrake",
  "driftbrake_version": "0.0.2",
  "database_type": "postgresql",
  "generated_at": "2026-05-19T10:30:00",
  "schemas": {
    "public": {
      "tables": {
        "users": {
          "columns": {
            "id": { "type": "INTEGER", "nullable": false, "primary_key": true, ... },
            "name": { "type": "VARCHAR", "nullable": true, ... }
          },
          "indexes": ["users_pkey"],
          "check_constraints": []
        }
      }
    }
  }
}
```

<br>

**Saídas possíveis:**
```
Conectando ao banco de dados e lendo o schema (public)...
[OK] Contrato de schema salvo em: schema.lock.json
     12 tabela(s) capturada(s) em 1 schema(s).
```

<br>

**Exemplo prático:**

```bash
driftbrake init --db-url "postgresql://postgres:secret@localhost:5432/mydb" --schemas public
```

```
Conectando ao banco... OK
Lendo schema: public
  customers     (4 colunas)
  orders        (6 colunas)
  order_items   (5 colunas)

Contrato gerado: schema.lock.json
  Schemas:  1
  Tabelas:  3
  Colunas:  15
```

<br>

### 2. `check` — Verificar se o banco mudou

Lê o banco de dados atual e compara com o contrato existente (`schema.lock.json`). Lista todas as diferenças encontradas, classifica cada uma por severidade e retorna um código de saída que pode ser usado em pipelines de CI/CD.

**Comando de rotina:** o `check` é o coração da ferramenta. Você roda antes de qualquer pipeline, migration ou deploy. Se ele retornar código 0, está tudo bem. Se retornar código 2, algo crítico mudou e o pipeline deve ser bloqueado.

**Comparar contrato → banco (e não banco → banco):** o contrato representa o estado *acordado* do banco. Ao comparar contra ele, você detecta desvios do que foi planejado, independente de quando ou como a mudança aconteceu. Execução:

#### `driftbrake check`

Compara o banco atual contra o contrato. É o comando central para uso em CI/CD.

```bash
driftbrake check \
  --db-url "$DATABASE_URL" \
  --contract schema.lock.json \
  --fail-on BREAKING \
  --json schema_diff.json \
  --html schema_report.html \
  --markdown schema_report.md
```

<br>

**Opções:**

| Opção | Padrão | O que faz |
|---|---|---|
| `--db-url` | lê do `.env` | URL de conexão com o PostgreSQL |
| `--contract` | `schema.lock.json` | Caminho do arquivo de contrato para comparar |
| `--fail-on` | `BREAKING` | Níveis que causam saída com código 2. Use `BREAKING,WARNING` para ser mais restritivo |
| `--json` | — | Caminho para salvar um relatório em JSON |
| `--html` | — | Caminho para salvar um relatório em HTML (visual, com tabelas coloridas) |
| `--markdown` | — | Caminho para salvar um relatório em Markdown |
| `--config` | — | Arquivo `.yml` com configurações adicionais (exclusões de tabelas, etc.) |

**Exit codes:** `0` compatível, `2` breaking change, `3` erro de conexão, `4` contrato ausente, `5` erro de configuração, `6` erro interno.

<br>

```bash
# Forma mais simples, usa schema.lock.json no diretório atual e variáveis do .env
driftbrake check

# Especificando tudo
driftbrake check \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --contract "schema.lock.json"

# Falhar também em warnings (mais restritivo)
driftbrake check --fail-on "BREAKING,WARNING"

# Gerar relatórios além da saída no terminal
driftbrake check \
  --json "relatorios/diff.json" \
  --html "relatorios/diff.html" \
  --markdown "relatorios/diff.md"

# Usando um arquivo de configuração (yml)
driftbrake check --config "driftbrake.yml"

# Comando completo para uso em CI
driftbrake check \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --contract "schema.lock.json" \
  --fail-on "BREAKING" \
  --html "relatorios/diff.html"
```

**Códigos de saída:**

| Código | Situação |
|---|---|
| `0` | Schema compatível — nenhuma mudança nos níveis configurados |
| `2` | Mudança detectada acima do limiar definido em `--fail-on` |
| `3` | Não foi possível conectar ao banco |
| `4` | Arquivo de contrato não encontrado ou inválido |
| `5` | Erro de configuração (ex: arquivo `.yml` inválido) |
| `6` | Erro interno inesperado |

<br>

**Usando em um script de pipeline:**
```bash
driftbrake check
if [ $? -ne 0 ]; then
  echo "Schema mudou — pipeline bloqueado."
  exit 1
fi
# continua com o pipeline...
```

<br>

**Exemplo prático (schema compatível):**

```bash
driftbrake check --db-url "$DATABASE_URL" --contract schema.lock.json
```

```
Conectando ao banco... OK
Comparando contra schema.lock.json...

DRIFTBRAKE CHECK PASSED

Resumo:
  BREAKING: 0
  WARNING:  0
  SAFE:     0

Nenhuma mudança detectada. Pipeline liberado.
```

<br>

**Exemplo prático (breaking change detectado):**

```bash
driftbrake check \
  --db-url "$DATABASE_URL" \
  --contract schema.lock.json \
  --fail-on BREAKING \
  --json schema_diff.json \
  --html schema_report.html
```

```
Conectando ao banco... OK
Comparando contra schema.lock.json...

DRIFTBRAKE CHECK FAILED

Resumo:
  BREAKING: 2
  WARNING:  1
  SAFE:     1

BREAKING
  public.customers    email              coluna removida
  public.orders       total_amount       tipo mudou: numeric → text

WARNING
  public.orders       customer_id        foreign key adicionada

SAFE
  public.customers    created_at         coluna nullable adicionada

JSON:  schema_diff.json
HTML:  schema_report.html

Pipeline bloqueado. (exit code 2)
```

<br>

**Exemplo prático (apenas warnings (pipeline continua)):**

```bash
driftbrake check --contract schema.lock.json --fail-on BREAKING
echo "Exit code: $?"
```

```
Conectando ao banco... OK
Comparando contra schema.lock.json...

DRIFTBRAKE CHECK WARNING

Resumo:
  BREAKING: 0
  WARNING:  2
  SAFE:     1

WARNING
  public.orders       status             default alterado: 'pending' → 'draft'
  public.customers    updated_at         NOT NULL removido

SAFE
  public.products     description        coluna nullable adicionada

Pipeline liberado com avisos. (exit code 0)

Exit code: 0
```

<br>

### 3. `diff` — Comparar duas versões de schema sem usar o contrato

Compara duas fontes de schema livremente, dois arquivos JSON, ou um arquivo JSON contra um banco ao vivo. Não usa nem modifica o `schema.lock.json`. É uma comparação pontual, exploratória.

**Separado do `check`:** o `check` tem uma função específica, validar o banco contra o contrato oficial. O `diff` é mais flexível: você pode comparar um snapshot de ontem com o banco de hoje, ou dois arquivos de ambientes diferentes (produção e homologação), sem comprometer o contrato.

**`--old` representa o "esperado" e `--new` o "atual":** a ferramenta sempre pensa em termos de "o que eu esperava" versus "o que encontrei". O arquivo `--old` é tratado como a referência (o que deveria ser) e `--new`/`--new-db` como o estado atual. Execução:

#### `driftbrake diff`

Compara dois schemas sem precisar de um contrato. Útil para comparar dois snapshots históricos ou um arquivo contra o banco atual.

**Arquivo vs arquivo:**

```bash
driftbrake diff \
  --old schema_before.json \
  --new schema_after.json \
  --json schema_diff.json
```

<br>

**Arquivo vs banco ao vivo:**

```bash
driftbrake diff \
  --old schema.lock.json \
  --new-db "$DATABASE_URL" \
  --html schema_diff.html
```

<br>

**Opções:**

| Opção | Padrão | O que faz |
|---|---|---|
| `--old` | obrigatório | Caminho para o arquivo JSON que representa o estado "esperado" / "antes" |
| `--new` | — | Caminho para o arquivo JSON que representa o estado "atual" / "depois" |
| `--new-db` | — | URL do banco de dados a ser usado como estado "atual" (alternativa ao `--new`) |
| `--json` | — | Caminho para salvar o relatório em JSON |
| `--html` | — | Caminho para salvar o relatório em HTML |

<br>

```bash
# Comparar dois arquivos JSON (ex: snapshot de ontem vs. snapshot de hoje)
driftbrake diff \
  --old "snapshots/schema_ontem.json" \
  --new "snapshots/schema_hoje.json"

# Comparar um arquivo JSON contra o banco ao vivo
driftbrake diff \
  --old "schema.lock.json" \
  --new-db "postgresql://user:pass@localhost:5432/mydb"

# Comparar e gerar relatórios
driftbrake diff \
  --old "schema_homolog.json" \
  --new-db "postgresql://user:pass@localhost:5432/mydb" \
  --json "diff_resultado.json" \
  --html "diff_resultado.html"
```

> [!CAUTION]
> Você deve informar `--new` **ou** `--new-db`, nunca os dois ao mesmo tempo. Se nenhum for informado, a ferramenta retorna erro.

<br>

**Exemplo prático (dois arquivos):**

```bash
driftbrake diff --old schema_before.json --new schema_after.json
```

```
Comparando schema_before.json → schema_after.json...

Resumo:
  BREAKING: 1
  WARNING:  2
  SAFE:     0

BREAKING
  public.payments     amount             tipo mudou: numeric(10,2) → text

WARNING
  public.payments     method             coluna adicionada (NOT NULL com default)
  public.orders       status             default alterado: NULL → 'open'
```

<br>

**Exemplo prático (arquivo e banco:)**

```bash
driftbrake diff --old schema.lock.json --new-db "$DATABASE_URL" --html diff_report.html
```

```
Lendo schema.lock.json...
Conectando ao banco... OK
Comparando...

Resumo:
  BREAKING: 0
  WARNING:  1
  SAFE:     2

WARNING
  public.customers    phone              NOT NULL removido

SAFE
  public.products     tags               coluna nullable adicionada
  public.products     sku                coluna nullable adicionada

HTML: diff_report.html
```

<br>

### 4. `snapshot` — Tirar uma foto do banco sem criar contrato

Conecta ao banco, lê o schema e salva em um arquivo JSON, igual ao `init`, mas com um nome de arquivo diferente por padrão (`schema.snapshot.json`) e sem a intenção de ser o contrato oficial.

**Função:** o `init` cria o contrato oficial do projeto. O `snapshot` serve para guardar estados intermediários, "como estava o banco na sexta-feira antes da migration", "estado do banco em homologação", "versão antes do deploy". Esses arquivos podem ser usados depois como `--old` no `diff` para investigar o que mudou.

**Por exemplo:** o `init` é o contrato oficial de comparação entre o estado atual do banco de dados. O `snapshot` é um registro, como um "backup" do momento em que você o executa, ele não é usado como comparação, apenas guarda como registro, cópia ou backup, etc. Execução:

#### `driftbrake snapshot`

Captura o schema atual do banco como um arquivo JSON sem comparar nada. Útil para auditoria e histórico.

```bash
driftbrake snapshot \
  --db-url "$DATABASE_URL" \
  --output historico/schema_2026-05-19.json \
  --schemas public
```

<br>

**Opções:**

| Opção | Padrão | O que faz |
|---|---|---|
| `--db-url` | lê do `.env` | URL de conexão com o PostgreSQL |
| `--output` | `schema.snapshot.json` | Caminho do arquivo de snapshot gerado |
| `--schemas` | `public` | Schemas do PostgreSQL a capturar |

<br>

```bash
# Snapshot básico do banco atual
driftbrake snapshot

# Salvando com nome descritivo
driftbrake snapshot --output "snapshots/antes_migration_2026_05_19.json"

# Snapshot de schemas específicos
driftbrake snapshot --schemas "public,analytics"

# Snapshot completo com credenciais explícitas
driftbrake snapshot \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --schemas "public" \
  --output "snapshots/schema_$(date +%Y%m%d).json"
```

> [!NOTE]
> ***Dica de uso:** criar um snapshot antes de cada migration é uma boa prática. Se algo der errado, você consegue fazer um `diff` para entender exatamente o que mudou.*

<br>

**Exemplo prático:**

```bash
driftbrake snapshot \
  --db-url "$DATABASE_URL" \
  --output historico/schema_2026-05-19.json \
  --schemas public,raw
```

```
Conectando ao banco... OK
Lendo schemas: public, raw

  public
    customers     (4 colunas)
    orders        (6 colunas)
    order_items   (5 colunas)

  raw
    raw_events    (8 colunas)
    raw_sessions  (5 colunas)

Snapshot salvo: historico/schema_2026-05-19.json
  Schemas:  2
  Tabelas:  5
  Colunas:  28
```

<br>

### 5. `update-contract` — Aceitar as mudanças e atualizar o contrato

Reconecta ao banco, lê o schema atual e sobrescreve o `schema.lock.json` com esse novo estado. Em outras palavras: "estou ciente das mudanças, elas são intencionais, e quero que passem a ser o novo contrato". Quando uma mudança é planejada e aprovada, uma migration legítima, uma refatoração de schema deliberada, o contrato precisa ser atualizado para refletir o novo estado. Sem esse comando, o `check` continuaria reportando as mudanças para sempre como se fossem problemas.

**Confirmação interativa:** sobrescrever o contrato é uma ação irreversível sem o git. A confirmação existe como proteção contra execuções acidentais.

**Comando `--yes`:** em ambientes de CI/CD não há terminal interativo. O `--yes` (ou `-y`) pula a confirmação para que o comando possa rodar em scripts automatizados após aprovação humana no processo de review. Execução:

#### `driftbrake update-contract`

Atualiza o `schema.lock.json` para refletir o estado atual do banco. Use após aprovar e aplicar uma mudança de schema intencional.

```bash
driftbrake update-contract \
  --db-url "$DATABASE_URL" \
  --contract schema.lock.json \
  --yes
```

<br>

**Opções:**

| Opção | Padrão | O que faz |
|---|---|---|
| `--db-url` | lê do `.env` | URL de conexão com o PostgreSQL |
| `--contract` | `schema.lock.json` | Caminho do contrato a ser sobrescrito |
| `--yes` / `-y` | `false` | Pula a pergunta de confirmação |
| `--schemas` | `public` | Schemas a capturar para o novo contrato |

> [!WARNING]
> **Atenção:** sem `--yes`, o comando pede confirmação explícita antes de sobrescrever o contrato.

<br>

```bash
# Atualizar o contrato com confirmação interativa
driftbrake update-contract

# Atualizar sem confirmação (para uso em scripts/CI após aprovação)
driftbrake update-contract --yes

# Especificando um contrato em outro caminho
driftbrake update-contract --contract "contratos/producao.lock.json"

# Atualizar schemas específicos
driftbrake update-contract --schemas "public,analytics"

# Comando completo
driftbrake update-contract \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --contract "schema.lock.json" \
  --schemas "public" \
  --yes
```

<br>

**Exemplo prático (modo não interativo (CI/CD):)**

```bash
driftbrake update-contract --db-url "$DATABASE_URL" --contract schema.lock.json --yes
```

```
Conectando ao banco... OK
Lendo schema atual...
Contrato atualizado: schema.lock.json
```

---
</details>

<br>

<details>
<summary><b><code>Atalho de Desenvolvimento</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

O repositório possui o arquivo `Makefile` com comandos de atalho:

```bash
pip install -e ".[dev]"
make test       # roda todos os testes
make lint       # verifica estilo
make check      # lint + typecheck + testes
```

---
</details>

<br>

<details>
<summary><b><code>Exit Codes</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

| Código | Significado |
|---|---|
| `0` | Sucesso — schema compatível ou operação concluída |
| `1` | Aviso em modo estrito (reservado) |
| `2` | Mudança crítica detectada — pipeline deve ser bloqueado |
| `3` | Erro de conexão com o banco de dados |
| `4` | Contrato ausente ou inválido |
| `5` | Erro de configuração |
| `6` | Erro interno inesperado |

> [!NOTE]
> CI/CD pode decidir sucesso ou falha exclusivamente pelo exit code.

---
</details>

<br>

<details>
<summary><b><code>Formato do contrato</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

O contrato é gerado pelo comando `init` e deve ser versionado no Git. Representa o schema que o pipeline espera encontrar.

```json
{
  "contract_version": "1.0",
  "generated_by": "driftbrake",
  "driftbrake_version": "0.0.2",
  "database_type": "postgresql",
  "generated_at": "2026-05-19T10:00:00",
  "schemas": {
    "public": {
      "tables": {
        "customers": {
          "columns": {
            "id": {
              "type": "integer",
              "nullable": false,
              "default": null,
              "primary_key": true,
              "unique": false,
              "foreign_key": false,
              "ordinal_position": 1
            },
            "email": {
              "type": "text",
              "nullable": false,
              "default": null,
              "primary_key": false,
              "unique": true,
              "foreign_key": false,
              "ordinal_position": 2
            }
          }
        }
      }
    }
  }
}
```

---
</details>

<br>

<details>
<summary><b><code>Formato dos relatórios gerados: JSON, HTML e Markdown</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

### JSON (`--json schema_diff.json`)

```json
{
  "status": "failed",
  "checked_at": "2026-05-19T10:00:00",
  "database_type": "postgresql",
  "summary": { "breaking": 2, "warning": 1, "safe": 3 },
  "changes": [
    {
      "severity": "BREAKING",
      "change_type": "column_removed",
      "schema": "public",
      "table": "customers",
      "column": "email",
      "message": "Column removed",
      "before": { "type": "text" },
      "after": null
    }
  ]
}
```

### HTML (`--html schema_report.html`)

Relatório visual com resumo geral, inspirado no modelo do ydata-profiling (antigo *Pandas Profiling*). Usa os templates em `templates/`.

### Markdown (`--markdown schema_report.md`)

Relatório em formato Markdown, para comentários automáticos em pull requests.

---
</details>

<br>

<details>
<summary><b><code>Arquivos do projeto</code></b> — <i>Clique aqui para visualizar</i></summary>

<br>

```
DriftBrake/
├── src/driftbrake/
│   ├── cli.py                        Comandos Typer (driftbrake)
│   ├── guard.py                      SchemaGuard (API de alto nível)
│   ├── models.py                     Dataclasses: ColumnSchema, TableSchema, DiffResult...
│   ├── exceptions.py                 Hierarquia de exceções
│   ├── readers/
│   │   ├── base.py                   Classe abstrata SchemaReader
│   │   ├── postgres.py               PostgresSchemaReader (SQLAlchemy Inspector)
│   │   └── json_reader.py            JsonSchemaReader (schema.lock.json)
│   ├── comparators/
│   │   └── schema_comparator.py      SchemaComparator (detecta diferenças)
│   ├── classifiers/
│   │   ├── impact_classifier.py      ImpactClassifier (atribui severidade)
│   │   └── type_compatibility.py     Matriz de compatibilidade de tipos
│   ├── reporters/
│   │   ├── terminal.py               Saída Rich no terminal
│   │   ├── json_report.py            Relatório JSON estável
│   │   ├── html_report.py            Relatório HTML (usa templates/)
│   │   └── markdown_report.py        Relatório Markdown
│   ├── contracts/
│   │   ├── loader.py                 Carrega e valida schema.lock.json
│   │   └── writer.py                 Gera schema.lock.json
│   └── config/
│       └── settings.py               Loader do driftbrake.yml
├── tests/                            57 testes unitários
├── examples/                         Pipeline Python, Airflow, dbt, GitHub Actions
├── templates/                        Templates HTML dos relatórios
├── pyproject.toml
├── Makefile
├── driftbrake.example.yml
├── README.md                         Introdução à ferramenta
├── DOCUMENTATION.md                  Documentação
└── CHANGELOG.md                      Histórico de versões
```

</details>

---
<br>

## A ferramenta

DriftBrake não é uma ferramenta de migration. Ele não aplica mudanças no banco, não gera scripts SQL e não gerencia versões de schema.

O DriftBrake atua **antes** da execução de pipelines, verificando se o banco real ainda respeita o contrato esperado pelos consumidores de dados. Ele detecta desvios, classifica o impacto e bloqueia execuções quando necessário, mas nunca altera o banco.

**Resumo:**

- Lê o schema do PostgreSQL
- Compara contra um contrato
- Classifica mudanças por impacto
- Bloqueia pipelines com breaking changes
- Gera relatórios JSON, HTML e Markdown

<br>

## Exemplo de Fluxo de trabalho

O `schema.lock.json` (contrato) vai ser gerado automaticamente quando você rodar o comando `init`.

```
banco de dados real
       │
       ▼
  [1] init          ← tira a "foto" do banco e salva como contrato
       │
       ▼
 schema.lock.json   ← esse arquivo é o contrato (contrato versionado no Git).
       │
       │    (o banco pode mudar ao longo do tempo)
       │
       ▼
  [2] check         ← compara o banco atual contra o contrato
       │
       ├── tudo igual → pipeline pode rodar
       └── mudança detectada → alerta ou bloqueio
```

Quando uma mudança é deliberada e aprovada, você usa `update-contract` para atualizar o contrato. Quando quer comparar dois estados sem tocar no contrato, usa `diff` ou `snapshot`.

<br>

## Glossário de termos

**Contrato (`schema.lock.json`):** o arquivo JSON que descreve como o banco *deve* ser. Funciona como um "lock file" (daí o nome), assim como `package-lock.json` trava as versões de pacotes, esse arquivo trava a estrutura do banco.

**BREAKING:** mudança que quebra consumidores existentes. Exemplos: remover uma coluna, mudar o tipo de `INTEGER` para `VARCHAR`, adicionar uma coluna `NOT NULL` sem valor padrão.

**WARNING:** mudança que merece atenção mas não necessariamente quebra nada agora. Exemplos: adicionar uma coluna `NOT NULL` com valor padrão, alterar um valor padrão.

**SAFE:** mudança sem impacto nos consumidores existentes. Exemplos: adicionar uma coluna nullable, criar uma nova tabela.

**Diff:** a diferença encontrada entre o contrato (o que era esperado) e o banco real (o que existe agora).

> [!NOTE]
> ***Contrato esperado & banco atual:** o comparador sempre trata o contrato como a "verdade combinada" e o banco como o "estado real". Se algo existe no banco mas não no contrato, é uma adição. Se existe no contrato mas sumiu do banco, é uma remoção.*


## Exemplo de uso inicial

**Criar o contrato inicial:**

```bash
driftbrake init --db-url "$DATABASE_URL" --output schema.lock.json
```

**Verificar antes do pipeline:**

```bash
driftbrake check \
  --db-url "$DATABASE_URL" \
  --contract schema.lock.json \
  --fail-on BREAKING \
  --json schema_diff.json \
  --html schema_report.html
```

**Atualizar o contrato após aprovar mudanças:**

```bash
driftbrake update-contract --db-url "$DATABASE_URL" --contract schema.lock.json
```

<br>

## Biblioteca Python

### Integração simples em um pipeline

```python
from driftbrake import SchemaGuard

def run_pipeline():
    print("Executando ETL...")

def main():
    SchemaGuard.from_env(
        contract_path="schema.lock.json",
        fail_on=["BREAKING"]
    ).assert_compatible()

    run_pipeline()

if __name__ == "__main__":
    main()
```

> [!NOTE]
> Se o banco tiver mudanças incompatíveis, `assert_compatible()` imprime o relatório, gera os arquivos e encerra o processo com `exit code 2`.

<br>

### Construção manual com `SchemaGuard`

```python
from driftbrake import SchemaGuard

guard = SchemaGuard(
    database_url="postgresql://user:pass@localhost:5432/mydb",
    contract_path="schema.lock.json",
    config_path="driftbrake.yml",   # opcional
    output_json="schema_diff.json",      # opcional
    output_html="schema_report.html",    # opcional
    output_markdown="schema_report.md",  # opcional
    fail_on=["BREAKING"],
    schemas=["public", "raw"],           # opcional, padrão: ["public"]
)

guard.assert_compatible()
run_pipeline()
```

### Inspecionando o resultado manualmente

```python
from driftbrake import SchemaGuard
from driftbrake.models import Severity

guard = SchemaGuard.from_env(contract_path="schema.lock.json")
result = guard.check()

print(f"Total de mudanças: {len(result.changes)}")
print(f"Breaking: {result.breaking_count}")
print(f"Warning:  {result.warning_count}")
print(f"Safe:     {result.safe_count}")

for change in result.changes:
    if change.severity == Severity.BREAKING:
        print(f"  BREAKING | {change.table_name}.{change.column_name}: {change.message}")

if result.has_breaking:
    guard.save_reports(result)
    raise SystemExit(2)
```

### Usando `SchemaComparator` diretamente

```python
from driftbrake.readers.postgres import PostgresSchemaReader
from driftbrake.readers.json_reader import JsonSchemaReader
from driftbrake.comparators.schema_comparator import SchemaComparator

expected = JsonSchemaReader("schema.lock.json").read()
current  = PostgresSchemaReader("postgresql://user:pass@host/db").read()

result = SchemaComparator().compare(expected=expected, current=current)

for change in result.changes:
    print(f"{change.severity.value:8} | {change.schema_name}.{change.table_name} | {change.message}")
```

<br>

## Funcionamento

O fluxo da versão atual:

```
schema.lock.json (contrato versionado no Git)
        │
        ▼
DriftBrake conecta no PostgreSQL
        │
        ▼
lê schema atual automaticamente
        │
        ▼
compara esperado e atual
        │
        ├── OK ──────────────────── pipeline executa
        │
        └── BREAKING ────────────── pipeline bloqueado
                                    ├── exibe no terminal
                                    ├── gera schema_diff.json
                                    └── gera schema_report.html
```

### Tipos de mudança detectados

A ferramenta detecta as seguintes categorias de alteração em cada comparação:

| Tipo | O que significa |
|---|---|
| `table_added` | Uma tabela nova apareceu no banco |
| `table_removed` | Uma tabela que existia sumiu do banco |
| `column_added` | Uma coluna nova foi adicionada a uma tabela existente |
| `column_removed` | Uma coluna foi removida de uma tabela existente |
| `type_changed` | O tipo de dado de uma coluna mudou (ex: `INTEGER` → `TEXT`) |
| `nullable_changed` | A coluna deixou de aceitar NULL ou passou a aceitar |
| `default_changed` | O valor padrão da coluna mudou ou foi removido |
| `primary_key_changed` | Uma coluna ganhou ou perdeu a chave primária |
| `unique_changed` | Uma constraint `UNIQUE` foi adicionada ou removida |
| `foreign_key_changed` | Uma chave estrangeira foi alterada |
| `foreign_key_added` | Uma chave estrangeira foi criada onde não havia |
| `ordinal_position_changed` | A posição da coluna na tabela mudou |
| `possible_rename` | Uma coluna foi removida e outra coluna semelhante foi adicionada na mesma tabela. A ferramenta trata isso apenas como uma suspeita de rename, nunca como confirmação. Sempre classificado como `WARNING`. |

> [!IMPORTANT]
> `possible_rename` é uma heurística, nunca uma confirmação. O DriftBrake sinaliza a suspeita quando uma coluna removida e uma coluna adicionada parecem compatíveis por tipo. A validação final deve ser feita por quem revisa a migration.

<br>

### Confiança do `possible_rename`

Cada ocorrência de `possible_rename` traz um campo `confidence` que indica o grau de certeza da heurística:

| Nível | Critério |
|---|---|
| `high` | Nome similar + mesmo tipo + posição ordinal próxima (diferença ≤ 2) |
| `medium` | Mesmo tipo + posição ordinal próxima (diferença ≤ 2) |
| `low` | Apenas tipo compatível (SAFE ou WARNING na matriz de tipos) |

**Exemplo no relatório JSON:**

```json
{
  "change_type": "possible_rename",
  "severity": "WARNING",
  "schema_name": "public",
  "table_name": "customers",
  "column_name": "customer_email",
  "old_value": "customer_email",
  "new_value": "email",
  "confidence": "medium",
  "description": "Column 'customer_email' removed and 'email' added with compatible type. Possible rename.",
  "suggestion": "If this is a rename, update the schema contract with the new column name 'email'."
}
```

**Regras importantes:**

- `possible_rename` **nunca** é classificado como `BREAKING` automaticamente, é sempre `WARNING`.
- Um `confidence: "high"` ainda é uma suspeita, não uma certeza.
- Sempre revise as migrations antes de aceitar um rename com `driftbrake update-contract`.

<br>

## Fluxo típico após uma migration:

```bash
# 1. Rodar a migration no banco
psql -U postgres -d mydb -f migration_001.sql

# 2. Verificar o que mudou
driftbrake check

# 3. Se as mudanças são as esperadas, aceitar e atualizar o contrato
driftbrake update-contract --yes

# 4. Commitar o novo contrato junto com a migration
git add schema.lock.json migration_001.sql
git commit -m "migration: adiciona coluna email_verificado na tabela users"
```

## Uso sem `--db-url` (via `.env`)

Em todos os comandos, a opção `--db-url` é opcional. Quando omitida, a ferramenta busca as credenciais na seguinte ordem:

1. Variável de ambiente `DATABASE_URL` (tem prioridade máxima)
2. Combinação de `DB_HOST` + `DB_PORT` + `DB_NAME` + `DB_USER` + `DB_PASSWORD`

Se você tiver o `.env` carregado no shell (por exemplo com `source .env` ou usando uma ferramenta como `dotenv`), pode rodar qualquer comando sem passar credenciais:

```bash
source .env
driftbrake check
driftbrake init
driftbrake snapshot
```

Ou simplesmente rodar de dentro do diretório do projeto — muitas ferramentas (como `uv run`, `direnv`, `docker-compose`) carregam o `.env` automaticamente.

<br>

## Classificação de Mudanças

### Tabelas

| Mudança | Severidade padrão |
|---|---|
| Tabela removida | BREAKING |
| Tabela adicionada | SAFE |

### Colunas

| Mudança | Severidade padrão |
|---|---|
| Coluna removida | BREAKING |
| Coluna adicionada (nullable) | SAFE |
| Coluna adicionada (NOT NULL sem default) | BREAKING |
| Coluna adicionada (NOT NULL com default) | WARNING |
| NOT NULL adicionado | BREAKING |
| NOT NULL removido | WARNING |
| Default alterado | WARNING |
| Primary key alterada | BREAKING |
| Unique constraint alterada | WARNING |
| Foreign key adicionada | WARNING |
| Foreign key alterada | BREAKING |
| Posição ordinal alterada | WARNING |
| Possível rename detectado | WARNING |

### Tipos PostgreSQL (matriz de compatibilidade)

| Conversão | Severidade |
|---|---|
| `varchar(50)` → `varchar(100)` | SAFE |
| `varchar(100)` → `varchar(50)` | BREAKING |
| `text` → `varchar(n)` | BREAKING |
| `varchar(n)` → `text` | SAFE |
| `integer` → `bigint` | WARNING |
| `bigint` → `integer` | BREAKING |
| `smallint` → `integer` | SAFE |
| `numeric(10,2)` → `numeric(12,2)` | SAFE |
| `numeric(12,2)` → `numeric(10,2)` | BREAKING |
| `numeric` → `text` | BREAKING |
| `date` → `timestamp` | WARNING |
| `timestamp` → `date` | BREAKING |

---
<br>

## Stack

- **SQLAlchemy** — reflection/inspection do PostgreSQL
- **Typer** — CLI
- **Rich** — output no terminal
- **Jinja2** — templates HTML
- **python-dotenv** — variáveis de ambiente
- **PyYAML** — configuração
- **pytest** — testes

## Licença

**MIT license**

## Autor

**Yuri Pontes** — Ex-Cabo do Exército Brasileiro em transição para engenharia de dados.

[LinkedIn](https://www.linkedin.com/in/yuri-pontes-4ba24a345/) · [GitHub](https://github.com/yurivski)