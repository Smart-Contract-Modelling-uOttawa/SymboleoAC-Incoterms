# Validation

Four layers (see ../STRATEGY.md §3). Start with the compile gate; add the rest
as specs land.

## 1. Static — compile gate (`tests/compile/`)

Every `specs/*.symboleo` must compile with **0 errors** using the SymboleoAC
compiler. The compiler reads a spec on stdin and prints JSON diagnostics
(`{issues, summary}`); exit 0 = clean, exit 1 = validation errors, and a
`--model` flag prints the structured model instead.

```bash
# one spec
cat specs/FOB.symboleo | java -jar "$CODEGEN_JAR"
# expect: {"summary":{"generatedFiles":N,"warnings":0,"errors":0}} and exit 0
```

Wire `CODEGEN_JAR` to a SymboleoAC compiler fat jar. Two ways to obtain it
(decide in the session):
- build from https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC2SC, or
- reuse the `codegen-cli` fat jar from SymboleoAC-Web (same upstream grammar).

CI (`.github/workflows/ci.yml`) runs this over every spec on push.

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
