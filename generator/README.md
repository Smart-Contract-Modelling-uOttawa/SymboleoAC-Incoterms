# Generator — ICC tables → SymboleoAC specs

Emits `specs/<CODE>.symboleo` for each Incoterms rule from:

- `incoterms.data.yaml` — the ICC cost/risk allocation tables (source of truth), and
- a library of **norm templates** (to be factored out of `specs/FOB.symboleo`).

Goal: 11 **structurally parallel** specs so coverage claims and differential
tests are apples-to-apples.

## Design (to implement in the spawned session)

1. **Templates.** Extract from FOB into parameterizable fragments:
   - domain: `Seller`, `Buyer`, `Carrier`, `Insurer?`, `Goods`, `BillOfLading`,
     and event templates (`ExportCleared`, `LoadedOnBoard`/delivery, `Paid`, …).
   - norms: `deliver`, `clearExport`, `contractCarriage`, `insure`,
     `provideDocuments`, `pay`, `takeDelivery`, `clearImport`, and the
     `suspend`/`resume`/`terminate` powers.
2. **Selection.** For each rule, the YAML row decides which templates are present
   and their debtor/creditor:
   - `delivery_point` → which delivery event marks risk transfer.
   - `export_clearance` / `import_clearance` → who owns the clearance obligations.
   - `seller_insurance` → include the `insure` obligation (+ `insurance_cover`).
   - `family` (sea vs any_mode) → carrier nomination vs first-carrier handover.
3. **Emit + verify.** Render deterministically, then compile every output
   (see ../CLAUDE.md). The generator must fail if any emitted spec does not
   compile with 0 errors.

## Implementation notes

- Keep the emitter simple and readable (a small script + string templates beats a
  heavy templating engine). Determinism matters — same input, byte-identical output.
- Do **not** encode the full 13-stage cost split as contract logic; carry it as
  data/comments and, at most, per-stage payment obligations. SymboleoAC has no
  cost algebra (see coverage matrix).
- Treat `specs/FOB.symboleo` as the golden reference: the generator's FOB output
  should be behaviorally equivalent to it.
