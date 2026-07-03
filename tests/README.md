# Validation

Four layers (see ../STRATEGY.md §3). Start with the compile gate; add the rest
as specs land.

## 1. Static — compile gate (`tests/compile/`)

Every `specs/*.symboleo` must compile with **0 errors**. The gate runs the whole
`specs/` dir through the SymboleoAC codegen and fails on any `summary.errors != 0`.
It has **two interchangeable backends**, selected by env:

| Backend | Env | Used by | Why |
|---------|-----|---------|-----|
| Local jar | `CODEGEN_JAR` = path to the codegen-cli fat jar | local dev, reproducibility | offline, no live service |
| Remote bridge | `BACKEND_URL` = deployed SymboleoAC-Web bridge | CI | no jar/Maven in CI; same codegen the Web IDE uses |

Both return the same JSON (`{summary:{generatedFiles,warnings,errors}, issues}`) —
the remote `/generate` endpoint just shells out to that jar.

```bash
# portable gate (jar OR remote), loops every spec:
CODEGEN_JAR=/path/to/symboleoac-codegen-cli-1.0.0-all.jar  tests/compile/run.sh
BACKEND_URL=https://159-69-216-244.sslip.io                tests/compile/run.sh

# Windows local dev (jar only):
$env:CODEGEN_JAR = "C:\...\symboleoac-codegen-cli-1.0.0-all.jar"; .\tests\compile\run.ps1

# one spec, by hand:
cat specs/FOB.symboleo | java -jar "$CODEGEN_JAR"
# expect: {"summary":{"generatedFiles":N,"warnings":0,"errors":0}} and exit 0
```

Obtain `CODEGEN_JAR` by building from
https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC2SC, or reuse the
`codegen-cli` fat jar from SymboleoAC-Web (same upstream grammar).

CI (`.github/workflows/ci.yml`) runs `run.sh` in **remote** mode over every spec
on push. Override the endpoint with a `BACKEND_URL` repo variable.

## 2. Structural (`tests/`)

Run the compiler with `--model` and assert, per spec:
- it contains the norms its coverage-matrix row requires;
- every `obligations.x` / `powers.x` cross-reference resolves;
- role/asset/event references are all bound.

## 3. Scenario execution (`tests/scenarios/`)

SymboleoAC generates runnable JS on `symboleoac-js-core`. Per rule, drive event
traces and assert final contract/norm state:
- **happy path** — all obligations fulfilled in order → contract fulfilled;
- **breach** — e.g. missed delivery activates the buyer's `terminate` power;
  late vessel nomination drives `suspend` → `resume`.

## 4. Differential

Encode inter-rule expectations from `generator/incoterms.data.yaml` as
assertions, e.g.:
- CIF/CIP have a seller `insure` obligation; FOB/FAS/FCA do not;
- risk passes strictly later under CFR than FOB on the same trace;
- D-rules place the delivery point at destination, not origin.

These catch generator drift when a template changes.
