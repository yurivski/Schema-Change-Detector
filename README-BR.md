
<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="imagens/db_banner_dark.svg">
    <img alt="DriftBrake-Banner" src="imagens/db_banner_white.svg" width="560">
  </picture>
</div>

<div align="center">

## Detecte, classifique e bloqueie drifts de schemas no PostgreSQL antes que seus pipelines sejam corrompidos.

</div>

[![Tests](https://github.com/yurivski/DriftBrake/actions/workflows/ci.yml/badge.svg)](https://github.com/yurivski/DriftBrake/actions/workflows/ci.yml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/driftbrake.svg)](https://pypi.org/project/driftbrake/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/driftbrake.svg?label=PyPI%20downloads)](https://pypi.org/project/driftbrake/)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/MIT-License-blue.svg)

**DriftBrake** é um projeto de pacote Python, que lê automaticamente o schema atual do banco de dados PostgreSQL, compara contra um contrato versionado, classifica mudanças por impacto e pode bloquear pipelines antes que eles quebrem em produção.

A ferramenta identifica bugs capazes de corromper ou quebrar pipelines em silêncio, antes do deploy em produção, com um conceito simples: você cria um "contrato" que descreve exatamente como seu banco deve ser. Antes de executar qualquer pipeline, a ferramenta compara o banco real com esse contrato e avisa (ou bloqueia) se algo mudou.

-----------------
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


**Regras importantes:**

- `possible_rename` **nunca** é classificado como `BREAKING` automaticamente, é sempre `WARNING`.
- Um `confidence: "high"` ainda é uma suspeita, não uma certeza.
- Sempre revise as migrations antes de aceitar um rename com `driftbrake update-contract`.

<br>

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