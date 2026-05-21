```text
DriftBrake
==========

DriftBrake is a Python tool that validates schema contracts before data pipelines run.

It reads the current PostgreSQL schema automatically, compares it against a versioned
contract, classifies changes by impact (BREAKING, WARNING, SAFE), and blocks pipelines
when incompatible changes are detected, before they cause failures in production.


The tool
========

  DriftBrake is not a migration tool. It does not apply changes to the database and does
  not generate SQL scripts.

  It runs BEFORE pipelines, verifying that the actual database still respects the
  contract expected by its data consumers.


Example
=======

  Data pipelines fail silently when the database schema changes without warning:

  - column removed or renamed
  - data type altered
  - NOT NULL added without a default
  - foreign key modified

  This tool runs an automatic validation before the pipeline starts and blocks the
  execution if the database is no longer compatible with the expected contract.

  Usage:

    driftbrake init     # creates the schema.lock.json contract
    driftbrake check    # checks whether the database has changed
    driftbrake diff     # compares two states without touching the contract


Documentation
=============

  - DOCUMENTATION.md - https://github.com/yurivski/driftbrake/blob/main/DOCUMENTATION.md
  - CHANGELOG.md - https://github.com/yurivski/driftbrake/blob/main/CHANGELOG.md
  - YML file - https://github.com/yurivski/driftbrake/blob/main/driftbrake.example.yml
```