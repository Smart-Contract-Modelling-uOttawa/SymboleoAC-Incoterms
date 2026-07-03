# Strategy — formalizing Incoterms 2020 in SymboleoAC

This document is the plan of record for the project and the paper. It defines
(1) how the 11 specs are generated consistently, (2) how coverage is analyzed,
and (3) how the specs are validated.

## 0. Thesis of the paper

SymboleoAC can express the **normative core** of Incoterms 2020 — the
obligations/powers lifecycle, the delivery↔payment↔risk sequencing, breach
remedies, and (uniquely vs. plain Symboleo) the **access-control policy** over
contract resources. It cannot natively express some **non-normative** aspects —
a cost algebra, first-class *risk*, insurance-cover levels, and the informal
"sufficient/customary" qualifiers. The paper reports both, with a per-article
traceability matrix and executable evidence.

## 1. Consistent generation (table-driven)

The 11 rules differ along a **small, tabulated** set of axes. Incoterms 2020
itself provides the data as two tables (reproduced in `generator/incoterms.data.yaml`):

- **Cost allocation** (13 stages: loading at origin → unloading at destination),
  each stage assigned to Seller / Buyer / both.
- **Risk transfer** — the single point where risk passes (seller premises,
  named place, alongside ship, **on board**, first carrier, destination
  place/terminal), i.e. the *delivery point*.

### Approach

1. **One shared domain ontology** (`specs/common/`): roles (`Seller`, `Buyer`,
   `Carrier`, `Insurer`, …), a parametric set of events
   (nomination, export/import clearance, carriage, loading/delivery, insurance,
   documents, payment, take-over), and assets (`Goods`, `BillOfLading`, …).
2. **A library of norm templates** — the reusable obligations/powers:
   `deliver`, `clearExport`, `contractCarriage`, `insure`, `provideDocuments`,
   `pay`, `takeDelivery`, `clearImport`, plus `suspend`/`resume`/`terminate`
   powers. Each template is parameterized by debtor/creditor and the
   delivery/deadline events.
3. **Per-rule configuration** = one row of the ICC tables → which templates are
   present, keyed to seller/buyer, with the delivery point (where risk passes)
   and the cost boundary set accordingly. Insurance templates switch on only for
   CIF/CIP (and their cover level recorded as data).
4. **Generator** (`generator/`): reads `incoterms.data.yaml` + the templates and
   emits `specs/<CODE>.symboleo`. Output is deterministic and formatted so the
   11 specs are **structurally parallel** — a prerequisite for apples-to-apples
   coverage claims and differential tests.

> Bootstrapping: FOB is hand-written and **compiles clean** (`specs/FOB.symboleo`).
> It is the reference the templates are factored out of. Recommended order to
> generalize: FOB → FAS → CFR → CIF (sea family), then FCA → CPT → CIP, then the
> D-family (DAP/DPU/DDP), then EXW.

## 2. Coverage analysis

`coverage/coverage-matrix.md`: rows **A1–A10** (seller) and **B1–B10** (buyer)
of the Incoterms article structure, columns = the 11 rules, cell ∈
{✅ expressible, ◐ partial, ❌ not expressible}, each with a short rationale and
a pointer to the modelling device used (or the gap).

Known gaps to foreground (the honest part of the paper):

- **Risk transfer (A3/B3)** — no first-class *risk* in SymboleoAC. Modelled
  indirectly: the delivery event triggers the payment obligation and the payment
  obligation **survives** termination, so cost/risk "passing on loading" is
  encoded structurally rather than semantically.
- **Cost allocation (A9/B9)** — obligations can assert "party X pays event Y",
  but there is no cost algebra for the 13-stage table; represented as data +
  per-stage payment obligations at best.
- **Insurance (A5/B5)** — presence of a seller insurance obligation is
  expressible (CIF/CIP); the *level* (Institute Cargo Clauses A/C, 110%) is only
  an attribute/constraint, not semantics.
- **Documents (A6/B6)** — bill of lading modelled as an asset + issuance event;
  *document of title* / transfer-of-documents semantics are not native.
- **Notices (A10/B10)** — "sufficient/customary notice" approximated by temporal
  predicates (`WhappensBefore`, deadlines); the vague qualifier is lost.

Strengths to sell: obligation/power lifecycle, sequencing via
`Happens/ShappensBefore/WhappensBefore/HappensWithin`, breach→suspend/resume/
terminate, and the **AC policy** (read/write/all/transfer permissions over
resources) — a differentiator over plain Symboleo.

## 3. Validation strategy (layered)

1. **Static (CI gate).** Every `specs/*.symboleo` compiles with **0 errors**
   using the SymboleoAC compiler (`codegen-cli`, see CLAUDE.md). Also check the
   formatter is idempotent.
2. **Structural.** A script over the compiler's `--model` JSON asserts each spec
   contains the norms its coverage row requires and that all cross-references
   resolve (no dangling `obligations.x` / `powers.x`).
3. **Scenario execution.** SymboleoAC generates runnable JS (on
   `symboleoac-js-core`). Per rule, drive event traces:
   - *happy path*: all obligations fulfilled in order → contract reaches
     fulfilled/terminated-successfully;
   - *breach paths*: e.g. missed delivery → buyer's `terminate` power becomes
     active; late vessel nomination → `suspend` then `resume`.
   Assert the resulting contract/norm states.
4. **Differential.** Turn the ICC tables into cross-rule assertions: e.g. CIF/CIP
   have a seller insurance obligation that FOB/FCA lack; risk passes strictly
   later under CFR than under FOB for the same trace; D-rules put delivery at
   destination. These catch generation drift.
5. **Legal/expert review.** Qualitative traceability from each modelled norm back
   to the ICC article text; recorded in the coverage matrix.

## 4. Paper outline (working)

1. Introduction — smart legal contracts, Incoterms, why a standard is a good
   coverage yardstick.
2. Background — SymboleoAC (norms, powers, AC policy), Incoterms 2020 structure.
3. Method — shared ontology + templates + table-driven generation.
4. The 11 specifications — walkthrough of representative rules (EXW, FOB, CIF, DDP).
5. Coverage analysis — the matrix + discussion of gaps.
6. Validation — static/structural/scenario/differential results.
7. Discussion — what a normative DSL can and cannot capture of a trade standard;
   proposed language extensions (risk, cost).
8. Related work, Conclusion.

## 5. Open decisions (revisit early)

- Paper format: LaTeX vs. Markdown-first.
- Whether to add optional roles (Insurer, Customs authority) to the shared
  ontology now or per-rule.
- How far to push cost modelling (data-only vs. per-stage payment obligations).
