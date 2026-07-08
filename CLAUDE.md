# SymboleoAC-Incoterms — agent notes

Project to formalize the 11 Incoterms 2020 rules as SymboleoAC contracts, with a
coverage analysis and validation, backing a paper. Read `STRATEGY.md` first.

## Status (updated 2026-07-05)

**All 11 rules are done and validated; CI is green.** Open PR: #1 (branch
`claude/vigilant-cohen-4c817b` → `main`). Where things live:

- `generator/generate.py` — table-driven generator (two axes: **term type E/F/C/D**
  × **family sea/any_mode**, plus feature switches), driven by
  `generator/incoterms.data.yaml`. Emits all of `specs/*.symboleo`. Roles carry
  `name, org, dept` (see grammar note below). `--check` = the regen guard.
- `specs/` — the 11 generated specs, each compiling **0 errors / 0 warnings**.
- `tests/compile/run.{sh,ps1}` — compile gate. CI uses the **remote bridge**
  (`BACKEND_URL`, default `https://159-69-216-244.sslip.io`); local dev uses the
  **jar** (`CODEGEN_JAR`). Same JSON either way.
- `tests/scenarios/` — **151 Node tests** (happy, breach/suspend, power
  coverage, ICC features, structural/differential, and the phase-1
  runtime-semantics witnesses) on the generated JS; `npm run coverage` (c8)
  ≈90% line. `symboleoac-js-core` is temporarily pinned to the
  `claude/phase1-runtime-semantics` git branch until it is merged/released.
- `coverage/coverage-matrix.md` — fully filled A1–A10/B1–B10 × 11, with
  cross-cutting differential notes.
- `deploy/README.md` — **verified** Hyperledger Fabric deployment guide (FOB was
  deployed on-chain and its access-control policy enforced); records the toolchain
  fixes. `deploy/issue-symboleoac2sc-dept.md` → filed as SymboleoAC2SC#1.
- `paper/` — the JURIX 2026 draft. **LOCAL ONLY — deliberately NOT committed**
  (git-excluded via the common-dir `.git/info/exclude`). Builds with
  `tectonic main.tex`. Do not `git add` it.

CI jobs: `compile` (remote gate), `regen-check` (`generate.py --check`),
`scenarios` (`node --test`). Keep all three green.

## What compiles: hard-won grammar facts (from the FOB seed)

All 11 `specs/*.symboleo` compile with **0 errors / 0 warnings**. (FOB was the
original hand-written golden reference, reproduced byte-for-byte; the specs are now
defined purely by `generator/generate.py` and pinned by the regen guard.) Facts
verified against the real compiler and the Xtext grammar
(https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC2SC):

- **Obligation:** `id: [trigger ->] O(debtor, creditor, antecedent, consequent) [with Controller ctrl]`.
  `O` or `Obligation`. debtor/creditor are **role** variables; trigger/antecedent/
  consequent are propositions.
- **Power:** `id: [trigger ->] P(creditor, debtor, antecedent, consequent) [with Controller ctrl]`.
  Note the **creditor-first** order (opposite of Obligation). The consequent is a
  *power function*: `Suspended|Resumed|Discharged|Terminated|Triggered(obligations.x)`
  or `Suspended|Resumed|Terminated(self)` for the contract (only these three for self).
- **Predicates:** `Happens(e)`, `HappensAfter(e, p|e2)`, `WhappensBefore(e, p|e2)`,
  `ShappensBefore(e, e2)`, `HappensWithin(e, interval|situation)`. A point can be a
  date attribute (`x.dueDate`) or an event variable. An interval is `Interval(p1,p2)`
  or a situation like `Suspension(obligations.x)`.
- **Event vs. situation names differ:** the *event* is `Violated/Fulfilled/…(obligations.x)`;
  the *situation/state* is `Violation/Fulfillment/Suspension/…(obligations.x)`. Use
  `Happens(Violated(obligations.x))` (event) but `HappensWithin(e, Suspension(obligations.x))`
  (situation).
- **Env attributes** (`Env foo: Type`) need **not** be assigned in a Declaration
  (they are runtime/external). Non-Env attributes generally are assigned.
- **Contract parameters** can be referenced directly in propositions (e.g.
  `paid.amount == price`).
- **Sections, in order:** Domain … endDomain, Contract … Declarations,
  [Preconditions], [Postconditions], Obligations, [Surviving Obligations],
  [Powers], [ACPolicy], [Constraints], endContract.
- **Powers may reference surviving obligations** via `obligations.x` (same
  namespace as main obligations at the syntax level): verified Wave 3 — the
  compiler resolves it, and the generated power-exercise transaction correctly
  routes to `contract.survivingObligations.x` (see `pRejectDocuments` →
  `Suspended(obligations.oPay)` and its runtime test in
  `tests/scenarios/icc-features.test.mjs`).
- `Date.add(datePoint, n, days)` — time units: seconds|minutes|hours|days|weeks|months|years.
  `TimeGranularity is days` is optional.
- **Roles need a `dept` attribute for access control.** Declare roles as
  `X isA Role with name: String, org: String, dept: String;`. The generated AC
  `authenticate` matches a caller cert's `HF.name`/`HF.role`/`organization`/
  `department` against a role and checks `department === objRole.dept._value`, so a
  role without `dept` cannot be authorized on-chain (returns "Unauthorized" /
  throws). Filed upstream as SymboleoAC2SC#1; the generator already emits it.

## Compile a spec (the validation gate)

The compiler reads a spec on stdin, prints JSON `{issues, summary}`; exit 0 =
clean, exit 1 = errors; `--model` prints the structured model instead.

```bash
cat specs/FOB.symboleo | java -jar "$CODEGEN_JAR"          # expect errors:0, exit 0
cat specs/FOB.symboleo | java -jar "$CODEGEN_JAR" --model  # structured model JSON
```

Obtaining `CODEGEN_JAR` (pick one, wire into CI):
- Build from SymboleoAC2SC (Maven), or
- Reuse SymboleoAC-Web's `codegen-cli` fat jar (same upstream grammar):
  `SymboleoAC-Web/codegen-cli/target/symboleoac-codegen-cli-1.0.0-all.jar`.

## Fast iteration in the browser

The Web IDE loads/validates/visualizes specs with no local setup:
https://smart-contract-modelling-uottawa.github.io/SymboleoAC-Web/ — Open a
`.symboleo` file, read live diagnostics, Generate JS, and inspect the Outline /
Domain / Rules / Policy views.

## Ground rules

1. Every spec in `specs/` must compile with 0 errors (CI-enforced).
2. Keep the 11 specs structurally parallel — generate from templates + the ICC
   tables in `generator/incoterms.data.yaml`, don't hand-diverge them.
3. Record every coverage finding in `coverage/coverage-matrix.md` as you go
   (with the modelling device or the gap + rationale).
4. Prefer verifying with a compile/scenario run over reasoning about the grammar.
5. **Never `git add` `paper/`** — the JURIX draft is deliberately local-only.
6. The two upstream codegen bugs this repo used to patch around (undeclared
   `isNewInstance` in `createSurvivingObligation_*`; arithmetic-in-consequent
   metadata SyntaxError, SymboleoAC2SC#3) are **fixed in the generator**
   (SymboleoAC-IDE / SymboleoAC-Web `claude/phase0-codegen-fixes`), and the
   codegen CLI now `node --check`s every emitted file (C4). `patchCodegen` is
   retired; tests need a jar/bridge built from those branches or later.
