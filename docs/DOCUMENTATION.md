<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" 
            srcset="https://raw.githubusercontent.com/yurivski/DriftBrake/main/docs/img/db_banner_dark.svg">
    <img alt="DriftBrake-Banner" 
         src="https://raw.githubusercontent.com/yurivski/DriftBrake/main/docs/img/db_banner_white.svg" 
         width="560">
  </picture>
</div>

-----------------
<br>

<div align="center">

**DriftBrake reads the current PostgreSQL schema automatically, compares it against a versioned
contract, classifies drifts by impact (BREAKING, WARNING, SAFE), and blocks pipelines
when incompatible changes are detected, before they cause failures in production.**

</div>

> [!NOTE]
> - Reads the PostgreSQL schema
> - Compares it against a contract
> - Classifies changes by impact
> - Blocks pipelines on breaking changes
> - Generates JSON, HTML, and Markdown reports

<br>

<div align="center">

### Shortcut by category: click the underlined title to expand.

</div>

<details>
<summary><b><code>INSTALLATION</code></b> — <i>Click here to view</i></summary>

#### #1

<br>

```bash
pip install -e .
```

To install with development dependencies:

```bash
pip install -e ".[dev]"
pre-commit install
```

Verify the installation:

```bash
driftbrake --help
```

Check the installed version:

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
<summary><b><code>Quick reference by situation</code></b> — <i>Click here to view</i></summary>

<br>

| Situation | Command |
|---|---|
| Using the tool for the first time | `driftbrake init` |
| Verify whether the database changed before running the pipeline | `driftbrake check` |
| Compare two states without touching the contract | `driftbrake diff --old file1.json --new file2.json` |
| Save the current database state as a future reference | `driftbrake snapshot --output snapshots/name.json` |
| A migration was applied and the changes are intentional | `driftbrake update-contract --yes` |
| View the change report in HTML | `driftbrake check --html report.html` |


### CLI commands at a glance

| Command | Description |
|---|---|
| `driftbrake init` | Generate `schema.lock.json` from the current database |
| `driftbrake check` | Compare the database against the contract and return an exit code |
| `driftbrake diff` | Compare two JSON files or a JSON file against the database |
| `driftbrake snapshot` | Capture the current schema without comparing |
| `driftbrake update-contract` | Update the contract to reflect the current state |

---
</details>

<br>

<details>
<summary><b><code>Configuring your .env file</code></b> — <i>Click here to view</i></summary>

<br>

The credentials below are an example of what your `.env` should contain. They are used automatically when you don't pass `--db-url`:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/mydb` |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `mydb` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | `secrets` |

**Database access:** the tool uses SQLAlchemy under the hood. When you run any command, it assembles the connection URL in the format `postgresql://user:password@host:port/database` and uses the `psycopg2` driver to connect. SQLAlchemy then uses the `Inspector`, an internal API that queries the PostgreSQL catalog (`information_schema` and `pg_catalog`) to read metadata about tables, columns, types, constraints, and indexes. None of your row data is read — only the structure.

**Connection priority:** if `DATABASE_URL` is defined in the environment, it takes full precedence. Only when it doesn't exist does the tool build the URL from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`.

---
</details>

<br>

<details>
<summary><b><code>Configuring the YML file</code></b> — <i>Click here to view</i></summary>

<br>

Create a `driftbrake.yml` file based on `driftbrake.example.yml`:

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

Pass the file to the CLI with `--config driftbrake.yml`, or to `SchemaGuard` with `config_path="driftbrake.yml"`.

---
</details>


<br>

<details>
<summary><b><code>Database connection</code></b> — <i>Click here to view</i></summary>

<br>

The tool accepts the database URL in three ways, in order of precedence:

**1. Direct CLI argument:**

```bash
driftbrake check --db-url "postgresql://user:pass@localhost:5432/mydb"
```

**2. Environment variable `DATABASE_URL`:**

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
driftbrake check
```

**3. Individual variables in `.env` or environment:**

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
<summary><b><code>Commands and example outputs</code></b> — <i>Click here to view</i></summary>

<br>

### 0. `--version` and `--info` — Check version and environment

#### `driftbrake --version`

Displays the installed DriftBrake version and exits.

```bash
driftbrake --version
```

```
DriftBrake 0.0.2
```

<br>

#### `driftbrake --info`

Displays full information about the runtime environment and exits. Useful when reporting issues.

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

### 1. `init` — Create the contract for the first time

Connects to your PostgreSQL, reads the complete database structure (tables, columns, types, constraints, indexes), and saves everything to a JSON file. That file becomes the contract — a "snapshot" of the current database state.

**First run:** without a contract, there's nothing to compare against. `init` is always the starting point. You run it once, commit the file to git, and from then on any database change can be detected. `init` comes before everything because it *creates* the reference point. It makes no sense to run `check` without a contract.

#### `driftbrake init`

Connects to the database, reads the current schema, and creates the contract `schema.lock.json`. This file should be versioned in Git.

```bash
driftbrake init \
  --db-url "$DATABASE_URL" \
  --schemas public \
  --output schema.lock.json
```

<br>

**Options:**

| Option | Default | What it does |
|---|---|---|
| `--db-url` | reads from `.env` | Full PostgreSQL connection URL |
| `--schemas` | `public` | Which PostgreSQL schemas to capture. Separate with commas for multiple |
| `--output` | `schema.lock.json` | Name and path of the generated contract file |

**Exit codes:** `0` success, `3` connection error.

<br>

```bash
# Simplest form — uses .env variables automatically
driftbrake init

# Explicitly specifying the database
driftbrake init --db-url "postgresql://user:pass@localhost:5432/mydb"

# Capturing specific schemas (besides public)
driftbrake init --schemas "public,analytics,staging"

# Saving the contract to a different path
driftbrake init --output "contracts/production_schema.lock.json"

# All together
driftbrake init \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --schemas "public" \
  --output "schema.lock.json"
```

<br>

**Example of the generated file:**
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

**Possible outputs:**
```
Connecting to the database and reading the schema (public)...
[OK] Schema contract saved to: schema.lock.json
     12 table(s) captured across 1 schema(s).
```

<br>

**Practical example:**

```bash
driftbrake init --db-url "postgresql://postgres:secret@localhost:5432/mydb" --schemas public
```

```
Connecting to the database... OK
Reading schema: public
  customers     (4 columns)
  orders        (6 columns)
  order_items   (5 columns)

Contract generated: schema.lock.json
  Schemas:  1
  Tables:   3
  Columns:  15
```

<br>

### 2. `check` — Verify whether the database has changed

Reads the current database and compares it to the existing contract (`schema.lock.json`). Lists every difference found, classifies each by severity, and returns an exit code suitable for CI/CD pipelines.

**Routine command:** `check` is the heart of the tool. You run it before any pipeline, migration, or deploy. If it returns exit code 0, you're good. If it returns 2, something critical has changed and the pipeline should be blocked.

**Compare contract → database (not database → database):** the contract represents the *agreed-upon* state of the database. Comparing against it lets you detect deviations from what was planned, regardless of when or how the change happened.

#### `driftbrake check`

Compares the current database against the contract. This is the central command for use in CI/CD.

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

**Options:**

| Option | Default | What it does |
|---|---|---|
| `--db-url` | reads from `.env` | PostgreSQL connection URL |
| `--contract` | `schema.lock.json` | Path to the contract file to compare against |
| `--fail-on` | `BREAKING` | Levels that trigger exit code 2. Use `BREAKING,WARNING` to be stricter |
| `--json` | — | Path to save a JSON report |
| `--html` | — | Path to save an HTML report (visual, with colored tables) |
| `--markdown` | — | Path to save a Markdown report |
| `--config` | — | YAML file with additional settings (table exclusions, etc.) |

**Exit codes:** `0` compatible, `2` breaking change, `3` connection error, `4` contract missing, `5` configuration error, `6` internal error.

<br>

```bash
# Simplest form — uses schema.lock.json in the current directory and .env variables
driftbrake check

# Specifying everything
driftbrake check \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --contract "schema.lock.json"

# Fail on warnings too (stricter)
driftbrake check --fail-on "BREAKING,WARNING"

# Generate reports alongside terminal output
driftbrake check \
  --json "reports/diff.json" \
  --html "reports/diff.html" \
  --markdown "reports/diff.md"

# Using a configuration file (yml)
driftbrake check --config "driftbrake.yml"

# Full command for CI use
driftbrake check \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --contract "schema.lock.json" \
  --fail-on "BREAKING" \
  --html "reports/diff.html"
```

**Exit codes:**

| Code | Situation |
|---|---|
| `0` | Schema compatible — no changes at the configured levels |
| `2` | Change detected above the threshold defined in `--fail-on` |
| `3` | Could not connect to the database |
| `4` | Contract file missing or invalid |
| `5` | Configuration error (e.g. invalid YAML file) |
| `6` | Unexpected internal error |

<br>

**Using in a pipeline script:**
```bash
driftbrake check
if [ $? -ne 0 ]; then
  echo "Schema changed — pipeline blocked."
  exit 1
fi
# continue with the pipeline...
```

<br>

**Practical example (compatible schema):**

```bash
driftbrake check --db-url "$DATABASE_URL" --contract schema.lock.json
```

```
Connecting to the database... OK
Comparing against schema.lock.json...

DRIFTBRAKE CHECK PASSED

Summary:
  BREAKING: 0
  WARNING:  0
  SAFE:     0

No changes detected. Pipeline cleared.
```

<br>

**Practical example (breaking change detected):**

```bash
driftbrake check \
  --db-url "$DATABASE_URL" \
  --contract schema.lock.json \
  --fail-on BREAKING \
  --json schema_diff.json \
  --html schema_report.html
```

```
Connecting to the database... OK
Comparing against schema.lock.json...

DRIFTBRAKE CHECK FAILED

Summary:
  BREAKING: 2
  WARNING:  1
  SAFE:     1

BREAKING
  public.customers    email              column removed
  public.orders       total_amount       type changed: numeric → text

WARNING
  public.orders       customer_id        foreign key added

SAFE
  public.customers    created_at         nullable column added

JSON:  schema_diff.json
HTML:  schema_report.html

Pipeline blocked. (exit code 2)
```

<br>

**Practical example (warnings only — pipeline continues):**

```bash
driftbrake check --contract schema.lock.json --fail-on BREAKING
echo "Exit code: $?"
```

```
Connecting to the database... OK
Comparing against schema.lock.json...

DRIFTBRAKE CHECK WARNING

Summary:
  BREAKING: 0
  WARNING:  2
  SAFE:     1

WARNING
  public.orders       status             default changed: 'pending' → 'draft'
  public.customers    updated_at         NOT NULL removed

SAFE
  public.products     description        nullable column added

Pipeline cleared with warnings. (exit code 0)

Exit code: 0
```

<br>

### 3. `diff` — Compare two schema versions without using the contract

Freely compares two schema sources: two JSON files, or a JSON file against a live database. It neither uses nor modifies `schema.lock.json`. It's an ad-hoc, exploratory comparison.

**Distinct from `check`:** `check` has a specific role — validate the database against the official contract. `diff` is more flexible: you can compare yesterday's snapshot to today's database, or two files from different environments (production and staging) without affecting the contract.

**`--old` represents the "expected" and `--new` the "current":** the tool always thinks in terms of "what I expected" versus "what I found." The `--old` file is treated as the reference (what it should be) and `--new`/`--new-db` as the current state.

#### `driftbrake diff`

Compares two schemas without needing a contract. Useful for comparing two historical snapshots, or a file against the current database.

**File vs file:**

```bash
driftbrake diff \
  --old schema_before.json \
  --new schema_after.json \
  --json schema_diff.json
```

<br>

**File vs live database:**

```bash
driftbrake diff \
  --old schema.lock.json \
  --new-db "$DATABASE_URL" \
  --html schema_diff.html
```

<br>

**Options:**

| Option | Default | What it does |
|---|---|---|
| `--old` | required | Path to the JSON file representing the "expected" / "before" state |
| `--new` | — | Path to the JSON file representing the "current" / "after" state |
| `--new-db` | — | Database URL to use as the "current" state (alternative to `--new`) |
| `--json` | — | Path to save the JSON report |
| `--html` | — | Path to save the HTML report |

<br>

```bash
# Compare two JSON files (e.g. yesterday's snapshot vs today's)
driftbrake diff \
  --old "snapshots/schema_yesterday.json" \
  --new "snapshots/schema_today.json"

# Compare a JSON file against the live database
driftbrake diff \
  --old "schema.lock.json" \
  --new-db "postgresql://user:pass@localhost:5432/mydb"

# Compare and generate reports
driftbrake diff \
  --old "schema_staging.json" \
  --new-db "postgresql://user:pass@localhost:5432/mydb" \
  --json "diff_result.json" \
  --html "diff_result.html"
```

> [!CAUTION]
> You must pass either `--new` **or** `--new-db`, never both at the same time. If neither is passed, the tool returns an error.

<br>

**Practical example (two files):**

```bash
driftbrake diff --old schema_before.json --new schema_after.json
```

```
Comparing schema_before.json → schema_after.json...

Summary:
  BREAKING: 1
  WARNING:  2
  SAFE:     0

BREAKING
  public.payments     amount             type changed: numeric(10,2) → text

WARNING
  public.payments     method             column added (NOT NULL with default)
  public.orders       status             default changed: NULL → 'open'
```

<br>

**Practical example (file and database):**

```bash
driftbrake diff --old schema.lock.json --new-db "$DATABASE_URL" --html diff_report.html
```

```
Reading schema.lock.json...
Connecting to the database... OK
Comparing...

Summary:
  BREAKING: 0
  WARNING:  1
  SAFE:     2

WARNING
  public.customers    phone              NOT NULL removed

SAFE
  public.products     tags               nullable column added
  public.products     sku                nullable column added

HTML: diff_report.html
```

<br>

### 4. `snapshot` — Capture a snapshot of the database without creating a contract

Connects to the database, reads the schema, and saves it to a JSON file — just like `init`, but with a different default filename (`schema.snapshot.json`) and without the intent of being the official contract.

**Purpose:** `init` creates the official contract of the project. `snapshot` is for keeping intermediate states — "how the database looked Friday before the migration," "state of the staging database," "version before the deploy." These files can later be used as `--old` in `diff` to investigate what changed.

**In other words:** `init` is the official contract for comparing against the current database state. `snapshot` is a record — like a "backup" of the moment you ran it. It isn't used as a comparison reference; it just stores a copy, like a record or backup.

#### `driftbrake snapshot`

Captures the current database schema as a JSON file without comparing anything. Useful for auditing and history.

```bash
driftbrake snapshot \
  --db-url "$DATABASE_URL" \
  --output history/schema_2026-05-19.json \
  --schemas public
```

<br>

**Options:**

| Option | Default | What it does |
|---|---|---|
| `--db-url` | reads from `.env` | PostgreSQL connection URL |
| `--output` | `schema.snapshot.json` | Path of the generated snapshot file |
| `--schemas` | `public` | PostgreSQL schemas to capture |

<br>

```bash
# Basic snapshot of the current database
driftbrake snapshot

# Saving with a descriptive name
driftbrake snapshot --output "snapshots/before_migration_2026_05_19.json"

# Snapshot of specific schemas
driftbrake snapshot --schemas "public,analytics"

# Full snapshot with explicit credentials
driftbrake snapshot \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --schemas "public" \
  --output "snapshots/schema_$(date +%Y%m%d).json"
```

> [!NOTE]
> ***Usage tip:** creating a snapshot before every migration is good practice. If anything goes wrong, you can run a `diff` to see exactly what changed.*

<br>

**Practical example:**

```bash
driftbrake snapshot \
  --db-url "$DATABASE_URL" \
  --output history/schema_2026-05-19.json \
  --schemas public,raw
```

```
Connecting to the database... OK
Reading schemas: public, raw

  public
    customers     (4 columns)
    orders        (6 columns)
    order_items   (5 columns)

  raw
    raw_events    (8 columns)
    raw_sessions  (5 columns)

Snapshot saved: history/schema_2026-05-19.json
  Schemas:  2
  Tables:   5
  Columns:  28
```

<br>

### 5. `update-contract` — Accept the changes and update the contract

Reconnects to the database, reads the current schema, and overwrites `schema.lock.json` with this new state. In other words: "I'm aware of the changes, they are intentional, and I want them to become the new contract." When a change is planned and approved — a legitimate migration, a deliberate schema refactor — the contract needs to be updated to reflect the new state. Without this command, `check` would keep reporting the changes forever as if they were problems.

**Interactive confirmation:** overwriting the contract is irreversible without git. The confirmation exists as protection against accidental runs.

**`--yes` flag:** in CI/CD environments there is no interactive terminal. `--yes` (or `-y`) skips the confirmation so the command can run in automated scripts after human approval in the review process.

#### `driftbrake update-contract`

Updates `schema.lock.json` to reflect the current database state. Use after approving and applying an intentional schema change.

```bash
driftbrake update-contract \
  --db-url "$DATABASE_URL" \
  --contract schema.lock.json \
  --yes
```

<br>

**Options:**

| Option | Default | What it does |
|---|---|---|
| `--db-url` | reads from `.env` | PostgreSQL connection URL |
| `--contract` | `schema.lock.json` | Path to the contract to overwrite |
| `--yes` / `-y` | `false` | Skips the confirmation prompt |
| `--schemas` | `public` | Schemas to capture for the new contract |

> [!WARNING]
> **Warning:** without `--yes`, the command asks for explicit confirmation before overwriting the contract.

<br>

```bash
# Update the contract with interactive confirmation
driftbrake update-contract

# Update without confirmation (for scripts/CI after approval)
driftbrake update-contract --yes

# Specifying a contract at a different path
driftbrake update-contract --contract "contracts/production.lock.json"

# Update specific schemas
driftbrake update-contract --schemas "public,analytics"

# Full command
driftbrake update-contract \
  --db-url "postgresql://user:pass@localhost:5432/mydb" \
  --contract "schema.lock.json" \
  --schemas "public" \
  --yes
```

<br>

**Practical example (non-interactive mode (CI/CD)):**

```bash
driftbrake update-contract --db-url "$DATABASE_URL" --contract schema.lock.json --yes
```

```
Connecting to the database... OK
Reading current schema...
Contract updated: schema.lock.json
```

---
</details>

<br>

<details>
<summary><b><code>Development shortcuts</code></b> — <i>Click here to view</i></summary>

<br>

The repository ships with a `Makefile` for common tasks:

```bash
pip install -e ".[dev]"
make test       # run all tests
make lint       # check style
make check      # lint + typecheck + tests
```

---
</details>

<br>

<details>
<summary><b><code>Exit Codes</code></b> — <i>Click here to view</i></summary>

<br>

| Code | Meaning |
|---|---|
| `0` | Success — schema compatible or operation completed |
| `1` | Warning in strict mode (reserved) |
| `2` | Critical change detected — pipeline should be blocked |
| `3` | Database connection error |
| `4` | Contract missing or invalid |
| `5` | Configuration error |
| `6` | Unexpected internal error |

> [!NOTE]
> CI/CD can decide success or failure based exclusively on the exit code.

---
</details>

<br>

<details>
<summary><b><code>Contract format</code></b> — <i>Click here to view</i></summary>

<br>

The contract is generated by `init` and should be versioned in Git. It represents the schema the pipeline expects to find.

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
<summary><b><code>Report formats: JSON, HTML, and Markdown</code></b> — <i>Click here to view</i></summary>

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

A visual report with a general summary, inspired by ydata-profiling (formerly *Pandas Profiling*). Uses the templates in `templates/`.

### Markdown (`--markdown schema_report.md`)

A Markdown-formatted report, suitable for automatic comments on pull requests.

---
</details>

<br>

<details>
<summary><b><code>Project files</code></b> — <i>Click here to view</i></summary>

<br>

```
DriftBrake/
├── src/driftbrake/
│   ├── cli.py                        Typer commands (driftbrake)
│   ├── guard.py                      SchemaGuard (high-level API)
│   ├── models.py                     Dataclasses: ColumnSchema, TableSchema, DiffResult...
│   ├── exceptions.py                 Exception hierarchy
│   ├── readers/
│   │   ├── base.py                   Abstract SchemaReader class
│   │   ├── postgres.py               PostgresSchemaReader (SQLAlchemy Inspector)
│   │   └── json_reader.py            JsonSchemaReader (schema.lock.json)
│   ├── comparators/
│   │   └── schema_comparator.py      SchemaComparator (detects differences)
│   ├── classifiers/
│   │   ├── impact_classifier.py      ImpactClassifier (assigns severity)
│   │   └── type_compatibility.py     Type compatibility matrix
│   ├── reporters/
│   │   ├── terminal.py               Rich terminal output
│   │   ├── json_report.py            Stable JSON report
│   │   ├── html_report.py            HTML report (uses templates/)
│   │   └── markdown_report.py        Markdown report
│   ├── contracts/
│   │   ├── loader.py                 Loads and validates schema.lock.json
│   │   └── writer.py                 Generates schema.lock.json
│   └── config/
│       └── settings.py               driftbrake.yml loader
├── tests/                            57 unit tests
├── examples/                         Python pipeline, Airflow, dbt, GitHub Actions
├── templates/                        HTML report templates
├── pyproject.toml
├── Makefile
├── driftbrake.example.yml
├── README.md                         Introduction to the tool
├── DOCUMENTATION.md                  Documentation
└── CHANGELOG.md                      Version history
```

</details>

---

<br>

<div align="center">

## Table of Contents

</div>

||||||
|-|-|-|-|-|
|**DESCRIPTION**|**LINK**|-|**DESCRIPTION**|**LINK**|
|**Create initial contract**|[Click Here](#initial-usage-example)|-|**Flow after migration**|[Click Here](#typical-flow-after-a-migration)|
|**Import as a library**|[Click Here](#python-library)|-|**Direct connection via `.env`**|[Click Here](#usage-without---db-url-via-env)|
|**SchemaGuard class**|[Click Here](#manual-construction-with-schemaguard)|-|**Drift classification**|[Click Here](#drifts-classification)|
|**SchemaComparator class**|[Click Here](#using-schemacomparator-directly)|-|**Stack**|[Click Here](#stack)|
|**Workflow**|[Click Here](#how-it-works)|-|**License**|[Click Here](#license)|
|**Confidence level**|[Click Here](#possible_rename-confidence)|-|**Author**|[Click Here](#author)|

<br>

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

## Python library

### Simple pipeline integration

```python
from driftbrake import SchemaGuard

def run_pipeline():
    print("Running ETL...")

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
> If the database contains incompatible changes, `assert_compatible()` prints the report, generates the files, and exits the process with `exit code 2`.

<br>

### Manual construction with `SchemaGuard`

```python
from driftbrake import SchemaGuard

guard = SchemaGuard(
    database_url="postgresql://user:pass@localhost:5432/mydb",
    contract_path="schema.lock.json",
    config_path="driftbrake.yml",   # optional
    output_json="schema_diff.json",      # optional
    output_html="schema_report.html",    # optional
    output_markdown="schema_report.md",  # optional
    fail_on=["BREAKING"],
    schemas=["public", "raw"],           # optional, default: ["public"]
)

guard.assert_compatible()
run_pipeline()
```

### Inspecting the result manually

```python
from driftbrake import SchemaGuard
from driftbrake.models import Severity

guard = SchemaGuard.from_env(contract_path="schema.lock.json")
result = guard.check()

print(f"Total changes: {len(result.changes)}")
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

### Using `SchemaComparator` directly

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

> [!IMPORTANT]
> `possible_rename` is a heuristic, never a confirmation. DriftBrake flags the suspicion when a removed column and an added column appear type-compatible. Final validation must be done by whoever reviews the migration.

<br>

### `possible_rename` confidence

Each `possible_rename` occurrence carries a `confidence` field indicating how certain the heuristic is:

| Level | Criteria |
|---|---|
| `high` | Similar name + same type + close ordinal position (difference ≤ 2) |
| `medium` | Same type + close ordinal position (difference ≤ 2) |
| `low` | Only type-compatible (SAFE or WARNING in the type matrix) |

**Example in the JSON report:**

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

**Important rules:**

- `possible_rename` is **never** automatically classified as `BREAKING` — always `WARNING`.
- A `confidence: "high"` is still a suspicion, not a certainty.
- Always review migrations before accepting a rename with `driftbrake update-contract`.

<br>

## Typical flow after a migration:

```bash
# 1. Run the migration on the database
psql -U postgres -d mydb -f migration_001.sql

# 2. Check what changed
driftbrake check

# 3. If the changes are expected, accept them and update the contract
driftbrake update-contract --yes

# 4. Commit the new contract alongside the migration
git add schema.lock.json migration_001.sql
git commit -m "migration: add email_verified column to users table"
```

## Usage without `--db-url` (via `.env`)

In every command, `--db-url` is optional. When omitted, the tool looks for credentials in the following order:

1. Environment variable `DATABASE_URL` (highest priority)
2. Combination of `DB_HOST` + `DB_PORT` + `DB_NAME` + `DB_USER` + `DB_PASSWORD`

If you have `.env` loaded in the shell (e.g. with `source .env` or a tool like `dotenv`), you can run any command without passing credentials:

```bash
source .env
driftbrake check
driftbrake init
driftbrake snapshot
```

Or simply run from inside the project directory — many tools (such as `uv run`, `direnv`, `docker-compose`) load `.env` automatically.

<br>

## Drifts classification

### Tables

| Drifts | Default severity |
|---|---|
| Table removed | BREAKING |
| Table added | SAFE |

### Columns

| Drifts | Default severity |
|---|---|
| Column removed | BREAKING |
| Column added (nullable) | SAFE |
| Column added (NOT NULL without default) | BREAKING |
| Column added (NOT NULL with default) | WARNING |
| NOT NULL added | BREAKING |
| NOT NULL removed | WARNING |
| Default changed | WARNING |
| Primary key changed | BREAKING |
| Unique constraint changed | WARNING |
| Foreign key added | WARNING |
| Foreign key changed | BREAKING |
| Ordinal position changed | WARNING |
| Possible rename detected | WARNING |

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