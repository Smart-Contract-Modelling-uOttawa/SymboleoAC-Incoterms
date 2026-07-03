# Coverage matrix — Incoterms 2020 articles × SymboleoAC

Legend: **✅** expressible · **◐** partial / approximated · **❌** not natively
expressible · **—** not applicable for this rule.

Columns are the 11 rules. Fill a column when its spec lands. FOB is seeded from
`specs/FOB.symboleo`; the rest are placeholders (`?`).

## Seller obligations (A1–A10)

| Art. | Obligation | Device in SymboleoAC | EXW | FCA | CPT | CIP | DAP | DPU | DDP | FAS | FOB | CFR | CIF |
|------|-----------|----------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A1 | General obligations (goods + invoice conform) | precondition / asset attributes | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| A2 | Delivery (delivery point) | `oDeliver` obligation; delivery event | ? | ? | ? | ? | ? | ? | ? | ✅ | ✅ | ✅ | ✅ |
| A3 | Transfer of risks | **no first-class risk**; via delivery trigger + surviving pay | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| A4 | Carriage | carriage event / obligation (seller side for C/D rules) | ? | ? | ? | ? | ? | ? | ? | — | — | ✅ | ✅ |
| A5 | Insurance | seller insurance obligation (CIF/CIP); level = attribute only | ? | ? | ? | ✅? | ? | ? | ? | — | — | — | ◐ |
| A6 | Delivery / transport document | `BillOfLading` asset + issuance event + `oProvideDocuments` | ? | ? | ? | ? | ? | ? | ? | ✅ | ✅ | ✅ | ✅ |
| A7 | Export/import clearance | `oExportClearance` obligation | ? | ? | ? | ? | ? | ? | ? | ✅ | ✅ | ✅ | ✅ |
| A8 | Checking / packaging / marking | asset attributes / constraints | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| A9 | Allocation of costs | **no cost algebra**; per-stage data / payment obligations | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| A10 | Notices | temporal predicates; "sufficient" lost | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |

## Buyer obligations (B1–B10)

| Art. | Obligation | Device in SymboleoAC | EXW | FCA | CPT | CIP | DAP | DPU | DDP | FAS | FOB | CFR | CIF |
|------|-----------|----------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| B1 | General obligations (pay the price) | `oPay` (surviving) obligation | ? | ? | ? | ? | ? | ? | ? | ✅ | ✅ | ✅ | ✅ |
| B2 | Taking delivery | `oTakeDelivery` obligation | ? | ? | ? | ? | ? | ? | ? | ✅ | ✅ | ✅ | ✅ |
| B3 | Transfer of risks | see A3; buyer bears risk after delivery point | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| B4 | Carriage | buyer contracts carriage (F-rules) via nomination | ? | ? | ? | ? | ? | ? | ? | ✅ | ✅ | — | — |
| B5 | Insurance | buyer insurance (or none) | ? | ? | ? | ? | ? | ? | ? | — | — | — | — |
| B6 | Proof of delivery | accept documents; event | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| B7 | Export/import clearance | buyer import clearance obligation | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| B8 | Inspection of goods | inspection event / obligation | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| B9 | Allocation of costs | see A9 | ? | ? | ? | ? | ? | ? | ? | ◐ | ◐ | ◐ | ◐ |
| B10 | Notices | vessel nomination + notice (`oNominateVessel`) | ? | ? | ? | ? | ? | ? | ? | ✅ | ✅ | ◐ | ◐ |

## Cross-cutting findings (running list)

- **Risk (A3/B3)** is the central limitation — SymboleoAC has no risk primitive.
  Modelled structurally (delivery triggers payment; payment survives). Candidate
  language extension for the Discussion section.
- **Cost (A9/B9)** — the 13-stage cost split is data, not semantics; SymboleoAC
  can attach payment obligations per stage but has no aggregation.
- **AC policy** — no direct Incoterms counterpart, but a genuine strength worth a
  subsection (who may read/write which resource, e.g. the bill of lading).
- **FOB vs FAS** (first differential) — identical coverage *pattern*, but the
  modelling device differs, faithfully (approach A): FOB delivers **on board**
  with a carrier-issued **bill of lading** in the seller's A6 document norm; FAS
  delivers **alongside** and the seller owes only the **usual proof of delivery
  alongside** (no `Carrier`/`BillOfLading` in the spec). So the A6 "Device"
  column above is the *FOB* device; FAS's A6 ✅ is via the `DocumentsProvided`
  proof-of-delivery event. The delivery-point difference (on board vs alongside)
  is the kind of inter-rule invariant the differential tests will assert.
- **F-terms vs C-terms** (CFR/CIF) — the second, sharper differential. F-terms
  (FOB/FAS) put carriage on the **buyer** (`oNominateVessel` + the
  suspend/resume-on-late-nomination powers), so **A4 = —, B4 = ✅**. C-terms
  (CFR/CIF) put carriage on the **seller** (`oContractCarriage`, replacing the
  nomination machinery with a `pTerminateNoCarriage` power), so the flip is
  **A4 = ✅, B4 = —**. Crucially, C-terms are where the **risk point and cost
  point diverge**: risk still passes **on board at shipment** (same `oDeliver` as
  FOB), while the seller's cost boundary runs to the **destination** port — a
  divergence SymboleoAC captures only *structurally* (delivery-on-board triggers
  the surviving payment; freight-to-destination is carried as data), never as a
  cost/risk semantics. This is the headline example for the paper's A3/A9 gaps.
- **Insurance (A5, CIF)** — `oInsure` makes the seller's insurance *obligation*
  first-class (✅ for presence), and `pTerminateNoInsurance` gives it a remedy,
  but the **cover level** (ICC (C), 110%) is only an `InsuranceObtained.coverLevel`
  data attribute — hence **◐**, not ✅: the level is recorded, not enforced as
  semantics.
