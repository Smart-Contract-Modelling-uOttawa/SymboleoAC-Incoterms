# SymboleoAC-Incoterms — agent notes

Project to formalize the 11 Incoterms 2020 rules as SymboleoAC contracts, with a
coverage analysis and validation, backing a paper. Read `STRATEGY.md` first.

## What compiles: hard-won grammar facts (from the FOB seed)

`specs/FOB.symboleo` compiles with **0 errors / 0 warnings** and is the golden
reference. Facts verified against the real compiler and the Xtext grammar
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
- **Powers/ACPolicy should reference *main* obligations** via `obligations.x`;
  whether surviving obligations are resolvable from `obligations.` is unverified —
  avoid pointing a power at a surviving obligation until checked.
- `Date.add(datePoint, n, days)` — time units: seconds|minutes|hours|days|weeks|months|years.
  `TimeGranularity is days` is optional.

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
