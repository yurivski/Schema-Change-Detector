<div align="center">

# Changelog

</div>

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<br>

## [0.0.3] (2026-05-23)

### Changed

- **README completely redesigned.** New layout with banner, badges (CI status, 
  PyPI version, downloads, Python version, license), and prominent link to 
  full documentation. Visual identity aligned with mature open source projects.
- **README and DOCUMENTATION available in two languages.** English version 
  (`README.md`, `DOCUMENTATION.md`) and Brazilian Portuguese version 
  (`README-BR.md`, `DOCUMENTATION-BR.md`).
- **Documentation reorganized.** Technical reference moved from README to 
  DOCUMENTATION, keeping README focused on showcase.

No code or behavior changes from 0.0.2.

---

## [0.0.2] (2026-05-22)

### Added

- **`driftbrake --version`:** displays the installed version and exits. Example:
  ```
  DriftBrake 0.0.2
  ```
- **`driftbrake --info`:** displays full environment information and exits. Example:
  ```
  DriftBrake 0.0.2
  Python 3.13.5
  Platform Linux-6.5.0-parrot
  SQLAlchemy 2.0.49
  ```
- **pre-commit:** every `git commit` runs ruff automatically. If a lint error is found, the commit is blocked until you fix it.
- **Visual separators in the summary:** the summary table in the terminal now displays separators between rows (`show_lines=True`), making it easier to read.
- **Collapse when no changes exist:** when the comparison returns 0 changes, the output collapses to a single line: `Schemas compatible — 0 changes detected.`

### Changed

- **CLI language:** all CLI command labels, descriptions, and messages were translated to English. Internal code comments remain in Brazilian Portuguese.

### Fixed

- **`load_dotenv()` not called automatically:** the CLI now calls `load_dotenv()` before any environment variable lookup, ensuring `.env` files in the current directory are loaded automatically. Previous behavior required `source .env` manually in the shell.
- **Outdated `driftbrake_version` in contracts:** the `driftbrake_version` field in `schema.lock.json` is now read dynamically via `importlib.metadata.version()`, eliminating the hardcoded `"0.2.0"` that was generated regardless of the installed version.
- **"DRIFTBRAKE CHECK FAILED" message in `diff` output:** the `diff` command is exploratory and always returns exit code 0. The final message now displays "DIFFERENCES DETECTED" (in yellow) instead of "DRIFTBRAKE CHECK FAILED" (in red), eliminating the confusion between actual failure and informational result.
- **HTML templates outside the package (not included in the wheel):** the `templates/` folder was moved into `src/driftbrake/templates/`. `html_report.py` now loads templates via `PackageLoader("driftbrake", "templates")`, ensuring it works in both editable install and published wheel. `pyproject.toml` was updated with `include` for `.html` files.

---

## [0.0.1] (2026-05-21)

Initial release published to reserve the `driftbrake` name on PyPI.

### Added

**Python package**

- `src/driftbrake/` structure with all package modules.
- `pyproject.toml` with declared dependencies, project metadata, and `driftbrake` entry point.
- Working `pip install -e .` command.
- Python 3.10+ support (replaces `StrEnum` with `str + Enum`).
- Hatchling build exclusion configuration.
- `[project.urls]` and complete classifiers added to `pyproject.toml`.
- README translated to English.

**CLI with Typer (`driftbrake`)**

- `init` command: connects to the database and generates `schema.lock.json` (versionable contract).
- `check` command: compares the live database against the contract and returns a deterministic exit code.
- `diff` command: compares two JSON files or a file against the database.
- `snapshot` command: captures the current schema without comparing (replaces manual `exportador.py`).
- `update-contract` command: updates the contract after approving changes, with mandatory confirmation.

**Automatic PostgreSQL reading**

- `PostgresSchemaReader` using SQLAlchemy Inspector.
- Captures: columns, types, nullable, defaults, ordinal position, primary keys, foreign keys, unique constraints, check constraints, and indexes.
- Multi-schema support (`--schemas public,raw,analytics`).
- Accepts `DATABASE_URL` or individual variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

**Versioned contract (`schema.lock.json`)**

- Stable format with version, timestamp, database type, and nested schemas.
- Suitable for Git versioning.
- `ContractWriter` and `ContractLoader` for consistent reading and writing.

**Standardized internal models**

- `ColumnSchema`, `TableSchema`, `DatabaseSchema`, `SchemaChange`, `DiffResult`.
- Enums `Severity` (`BREAKING`, `WARNING`, `SAFE`) and `ChangeType` (15 change types).

**Source-independent comparator**

- `SchemaComparator` receives two `DatabaseSchema` objects without knowing whether they came from the database or a file.
- Detects: added/removed tables, added/removed columns, changed type, changed nullable, changed default, changed primary key, changed unique, added/changed foreign key, changed ordinal position.
- Possible rename detection: when a column is removed and another added with a compatible type in the same table, suggests rename as `WARNING`.

**Impact classifier**

- `ImpactClassifier` with rules configurable via YAML file.
- Rules can be individually overridden in `driftbrake.yml`.

**Intelligent type compatibility matrix**

- `type_compatibility.py` with logic for `VARCHAR(n)`, `NUMERIC(p,s)`, integers, dates, and generic types.
- Distinguishes widening (SAFE/WARNING) from narrowing (BREAKING) of size and precision.

**Reports**

- Terminal output with Rich: grouped by severity and table, with colors and final summary.
- Stable JSON (`schema_diff.json`) with status, summary, and list of changes with before/after.
- HTML using existing templates in `templates/` via Jinja2.
- Markdown for use in automatic pull request comments.

**`SchemaGuard` — API**

- `SchemaGuard(database_url, contract_path, ...)` for direct use in Python pipelines.
- `SchemaGuard.from_env(contract_path)` for automatic environment variable lookup.
- `check()` returns `DiffResult` without side effects.
- `assert_compatible()` blocks the process with the correct exit code if forbidden changes exist.
- `save_reports()` and `print_report()` for granular output control.

**YAML configuration file**

- `driftbrake.yml` supports `fail_on`, `warn_on`, schema filtering, ignored tables and columns, and rule overrides.
- `driftbrake.example.yml` included in the repository as reference.

**Professional exit codes**

- `0` compatible, `1` warning strict, `2` breaking, `3` connection, `4` contract, `5` configuration, `6` internal.

**Automated tests**

- 57 unit tests in `tests/unit/` covering comparator, classifier, and type matrix.
- Fixtures in `tests/fixtures/` for tests without database dependency.

**Project CI**

- `.github/workflows/ci.yml`: lint, typecheck, and tests on every push and pull request.

**Makefile**

- Commands: `install`, `test`, `lint`, `format`, `typecheck`, `check`.

### Changed

- JSON is no longer a mandatory step and became an optional output of the process.
- Comparison logic was decoupled from file reading: the comparator receives Python objects, not paths.
- The HTML report now uses Jinja2 instead of manual string replacement.
- Refactored dependencies: `psycopg2` moved to `[postgres]` extras.

### Deprecated

- `fonte/exportador.py`: replaced by `readers/postgres.py` and the `snapshot` command.
- `fonte/comparador.py`: replaced by `comparators/schema_comparator.py` and the `check` command.
- `fonte/relatorio.py`: replaced by `reporters/html_report.py`.
- `fonte/__init__.py`: no longer needed in the new package.
- `arquivos.py`: scaffolding script for the original structure, no longer useful in the current version.
- `requirements.txt`: replaced by `pyproject.toml`.

---

[0.0.3]: https://github.com/yurivski/DriftBrake/releases/tag/v0.0.3
[0.0.2]: https://github.com/yurivski/DriftBrake/releases/tag/v0.0.2
[0.0.1]: https://github.com/yurivski/DriftBrake/releases/tag/v0.0.1