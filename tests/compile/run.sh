#!/usr/bin/env bash
# Compile gate — every specs/*.symboleo must report errors:0.
#
# Two interchangeable backends, chosen by env (jar wins if both are set):
#   CODEGEN_JAR  path to the codegen-cli fat jar; compiles locally, offline,
#               fully reproducible (see ../../CLAUDE.md for how to obtain it).
#   BACKEND_URL  base URL of a deployed SymboleoAC-Web bridge; each spec is
#               POSTed as {"source": "..."} to $BACKEND_URL/generate.
#
# CI sets BACKEND_URL; local dev typically sets CODEGEN_JAR. Same JSON either way:
#   {"summary":{"generatedFiles":N,"warnings":W,"errors":E},"issues":[...]}
#
# Usage:  tests/compile/run.sh [specs_dir]      (default: specs)
# Exit:   0 = all specs clean; 1 = at least one has errors; 2 = misconfigured.
set -euo pipefail

specs_dir="${1:-specs}"
shopt -s nullglob
specs=("$specs_dir"/*.symboleo)
if [ ${#specs[@]} -eq 0 ]; then
  echo "no specs found in '$specs_dir'" >&2
  exit 1
fi

if [ -n "${CODEGEN_JAR:-}" ]; then
  mode="jar ($CODEGEN_JAR)"
elif [ -n "${BACKEND_URL:-}" ]; then
  mode="remote ($BACKEND_URL)"
  # Fail fast with a clear message if the bridge is unreachable.
  if ! curl -sS --max-time 20 "$BACKEND_URL/healthz" | grep -q '"ok":true'; then
    echo "backend not healthy at $BACKEND_URL/healthz" >&2
    exit 2
  fi
else
  echo "set CODEGEN_JAR (local jar) or BACKEND_URL (remote bridge)" >&2
  exit 2
fi
echo "compile gate — ${#specs[@]} spec(s), mode: $mode"

# Emit the compiler's JSON ({summary, issues, ...}) for one spec on stdout.
compile() {
  local f="$1"
  if [ -n "${CODEGEN_JAR:-}" ]; then
    # exit 1 on validation errors still prints valid JSON — keep it.
    java -jar "$CODEGEN_JAR" < "$f" || true
  else
    # On any transport failure, emit nothing so the caller marks this spec FAIL
    # (empty output -> errors:"ERR") instead of aborting the whole run.
    { jq -Rs '{source: .}' < "$f" \
        | curl -sS --max-time 60 -X POST "$BACKEND_URL/generate" \
               -H 'content-type: application/json' --data @- ; } || true
  fi
}

fail=0
for f in "${specs[@]}"; do
  out="$(compile "$f")"
  errors="$(printf '%s' "$out" | jq -r '.summary.errors // "ERR"' 2>/dev/null || echo ERR)"
  warnings="$(printf '%s' "$out" | jq -r '.summary.warnings // "?"' 2>/dev/null || echo '?')"
  if [ "$errors" = "0" ]; then
    printf 'OK    %-30s errors:0 warnings:%s\n' "$(basename "$f")" "$warnings"
  else
    printf 'FAIL  %-30s errors:%s\n' "$(basename "$f")" "$errors"
    printf '%s' "$out" | jq -r '.issues[]? | "  \(.severity) L\(.line):\(.column) \(.message)"' 2>/dev/null \
      || printf '  %s\n' "$out"
    fail=1
  fi
done

if [ "$fail" -eq 0 ]; then echo "all specs compile clean."; else echo "compile gate FAILED." >&2; fi
exit $fail
