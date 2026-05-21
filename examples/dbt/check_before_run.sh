#!/usr/bin/env bash
# check_before_run.sh
#
# Validates the database schema contract before running dbt.
# If breaking changes are detected, dbt is NOT executed.
#
# Usage:
#   DATABASE_URL="postgresql://user:pass@host/db" ./check_before_run.sh
#
# Environment variables:
#   DATABASE_URL    - Full PostgreSQL connection URL (required)
#   CONTRACT_PATH   - Path to schema.lock.json (default: schema.lock.json)
#   FAIL_ON         - Severity threshold (default: BREAKING)

set -euo pipefail

CONTRACT_PATH="${CONTRACT_PATH:-schema.lock.json}"
FAIL_ON="${FAIL_ON:-BREAKING}"
REPORT_JSON="reports/schema_diff_$(date +%Y%m%d_%H%M%S).json"
REPORT_HTML="reports/schema_diff_$(date +%Y%m%d_%H%M%S).html"

echo "========================================"
echo "  DriftBrake — Pre-dbt Check"
echo "========================================"
echo "Contract : $CONTRACT_PATH"
echo "Fail on  : $FAIL_ON"
echo ""

# Executa a verificação de schema
driftbrake check \
  --db-url "$DATABASE_URL" \
  --contract "$CONTRACT_PATH" \
  --fail-on "$FAIL_ON" \
  --json "$REPORT_JSON" \
  --html "$REPORT_HTML"

EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 0 ]; then
  echo ""
  echo "Schema is compatible. Running dbt..."
  echo ""
  dbt run "$@"
elif [ "$EXIT_CODE" -eq 2 ]; then
  echo ""
  echo "ERROR: Breaking schema changes detected. dbt run was NOT executed."
  echo "Review the schema diff report at: $REPORT_HTML"
  exit 2
else
  echo ""
  echo "ERROR: driftbrake exited with code $EXIT_CODE."
  exit "$EXIT_CODE"
fi
