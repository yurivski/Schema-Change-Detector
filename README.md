<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" 
            srcset="https://raw.githubusercontent.com/yurivski/DriftBrake/main/docs/img/db_banner_dark.svg">
    <img alt="DriftBrake-Banner" 
         src="https://raw.githubusercontent.com/yurivski/DriftBrake/main/docs/img/db_banner_white.svg" 
         width="560">
  </picture>
</div>

<div align="center">

## Detect, classify, and block schema drift in PostgreSQL before your pipelines break

</div>

[![Tests](https://github.com/yurivski/DriftBrake/actions/workflows/ci.yml/badge.svg)](https://github.com/yurivski/DriftBrake/actions/workflows/ci.yml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/driftbrake.svg)](https://pypi.org/project/driftbrake/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/driftbrake.svg?label=PyPI%20downloads)](https://pypi.org/project/driftbrake/)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/MIT-License-blue.svg)

**DriftBrake** is a Python package that automatically reads the current schema of a PostgreSQL database, compares it against a versioned contract, classifies drifts by impact, and can block pipelines before they break in production.

The tool catches bugs that could silently corrupt or break data pipelines before they reach production. The idea is simple: you create a "contract" describing exactly how your database should look. Before running any pipeline, DriftBrake compares the actual database against this contract and warns you (or blocks you) if anything has changed.

<br>

> **Documentation:** [US-Click here!](https://github.com/yurivski/DriftBrake/blob/main/docs/DOCUMENTATION.md) | [BR-Clique Aqui!](https://github.com/yurivski/DriftBrake/blob/main/docs/DOCUMENTATION-br.md)  
> **Readme versão BR:** [Clique aqui!](https://github.com/yurivski/DriftBrake/blob/main/README-br.md)  
> **Classification Audit:** [US-Click here!](https://github.com/yurivski/DriftBrake/blob/main/docs/AUDIT.md) | [BR-Clique Aqui!](https://github.com/yurivski/DriftBrake/blob/main/docs/AUDIT-br.md)     
> **Changelog:** [Click here!](https://github.com/yurivski/DriftBrake/blob/main/docs/LOGS/CHANGELOG.md)

## The tool

DriftBrake is not a migration tool. It doesn't apply changes to the database, doesn't generate SQL scripts, and doesn't manage schema versions.

DriftBrake runs **before** pipelines execute, verifying that the actual database still respects the contract expected by its data consumers. It detects deviations, classifies impact, and blocks execution when necessary — but never alters the database.

**Summary:**

- Reads the PostgreSQL schema
- Compares it against a contract
- Classifies changes by impact
- Blocks pipelines on breaking changes
- Generates JSON, HTML, and Markdown reports

<br>

## Example workflow

The `schema.lock.json` (the contract) is generated automatically when you run `init`.

```
actual database
       │
       ▼
  [1] init          ← takes the "snapshot" of the database and saves it as the contract
       │
       ▼
 schema.lock.json   ← this file is the contract (versioned in Git)
       │
       │    (the database may change over time)
       │
       ▼
  [2] check         ← compares the current database against the contract
       │
       ├── all equal → pipeline can run
       └── change detected → alert or block
```

When a change is deliberate and approved, use `update-contract` to update the contract. When you want to compare two states without touching the contract, use `diff` or `snapshot`.

<br>

## Glossary

**Contract (`schema.lock.json`):** the JSON file that describes how the database *should* look. It works as a "lock file" (hence the name) — just as `package-lock.json` pins package versions, this file pins the database structure.

**BREAKING:** a change that breaks existing consumers. Examples: removing a column, changing a type from `INTEGER` to `VARCHAR`, adding a `NOT NULL` column without a default.

**WARNING:** a change that deserves attention but doesn't necessarily break anything right now. Examples: adding a `NOT NULL` column with a default, changing a default value.

**SAFE:** a change with no impact on existing consumers. Examples: adding a nullable column, creating a new table.

**Diff:** the difference found between the contract (what was expected) and the actual database (what exists now).

> ***Expected contract & current database:** the comparator always treats the contract as the "agreed-upon truth" and the database as the "actual state." If something exists in the database but not in the contract, it's an addition. If it exists in the contract but is missing from the database, it's a removal.*


## Initial usage example

**Create the initial contract:**

```bash
driftbrake init --db-url "$DATABASE_URL" --output schema.lock.json
```

**Verify before the pipeline runs:**

```bash
driftbrake check \
  --db-url "$DATABASE_URL" \
  --contract schema.lock.json \
  --fail-on BREAKING \
  --json schema_diff.json \
  --html schema_report.html
```

**Update the contract after approving changes:**

```bash
driftbrake update-contract --db-url "$DATABASE_URL" --contract schema.lock.json
```

<br>

## How it works

The current flow:

```
schema.lock.json (contract versioned in Git)
        │
        ▼
DriftBrake connects to PostgreSQL
        │
        ▼
reads the current schema automatically
        │
        ▼
compares expected against current
        │
        ├── OK ──────────────────── pipeline runs
        │
        └── BREAKING ────────────── pipeline blocked
                                    ├── displays in terminal
                                    ├── generates schema_diff.json
                                    └── generates schema_report.html
```

### Change types detected

The tool detects the following categories of change in every comparison:

| Type | What it means |
|---|---|
| `table_added` | A new table appeared in the database |
| `table_removed` | A table that existed is gone from the database |
| `column_added` | A new column was added to an existing table |
| `column_removed` | A column was removed from an existing table |
| `type_changed` | A column's data type changed (e.g. `INTEGER` → `TEXT`) |
| `nullable_changed` | The column stopped accepting NULL or started accepting it |
| `default_changed` | The column's default value changed or was removed |
| `primary_key_changed` | A column gained or lost its primary key |
| `unique_changed` | A `UNIQUE` constraint was added or removed |
| `foreign_key_changed` | A foreign key was modified |
| `foreign_key_added` | A foreign key was created where there was none |
| `ordinal_position_changed` | The column's position in the table changed |
| `possible_rename` | A column was removed and a similar one was added in the same table. The tool only flags this as a suspicion of rename, never as a confirmation. Always classified as `WARNING`. |

> `possible_rename` is a heuristic, never a confirmation. DriftBrake flags the suspicion when a removed column and an added column appear type-compatible. Final validation must be done by whoever reviews the migration.

<br>

### `possible_rename` confidence

Each `possible_rename` occurrence carries a `confidence` field indicating how certain the heuristic is:

| Level | Criteria |
|---|---|
| `high` | Similar name + same type + close ordinal position (difference ≤ 2) |
| `medium` | Same type + close ordinal position (difference ≤ 2) |
| `low` | Only type-compatible (SAFE or WARNING in the type matrix) |


**Important rules:**

- `possible_rename` is **never** automatically classified as `BREAKING` — always `WARNING`.
- A `confidence: "high"` is still a suspicion, not a certainty.
- Always review migrations before accepting a rename with `driftbrake update-contract`.

<br>

### PostgreSQL types (compatibility matrix)

| Conversion | Severity |
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

- **SQLAlchemy** — PostgreSQL reflection/inspection
- **Typer** — CLI
- **Rich** — terminal output
- **Jinja2** — HTML templates
- **python-dotenv** — environment variables
- **PyYAML** — configuration
- **pytest** — tests

## License

**MIT license**

## Author

**Yuri Pontes** — Former Cabo (Corporal equivalent) - Brazilian Army, transitioning to data engineering.

[LinkedIn](https://www.linkedin.com/in/yuri-pontes-4ba24a345/) · [GitHub](https://github.com/yurivski)