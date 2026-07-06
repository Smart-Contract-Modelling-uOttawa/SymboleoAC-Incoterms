# Coverage matrix — Incoterms 2020 articles × SymboleoAC

Legend: **✅** expressible · **◐** partial / approximated · **❌** not natively
expressible · **—** not applicable for this rule.

Columns are the 11 rules. **All 11 columns are filled** — every `specs/*.symboleo`
is generated and compiles 0 errors / 0 warnings. The single shared "Device" column
names the *representative* device; where a rule models an article differently (e.g.
FAS/any-mode proof-of-delivery vs a bill of lading), see the cross-cutting notes.

## Seller obligations (A1–A10)

| Art. | Obligation | Device in SymboleoAC | EXW | FCA | CPT | CIP | DAP | DPU | DDP | FAS | FOB | CFR | CIF |
|------|-----------|----------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A1 | General obligations (goods + invoice conform) | precondition / asset attributes | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| A2 | Delivery (delivery point) | `oDeliver` obligation; delivery event | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A3 | Transfer of risks | **no first-class risk**; via delivery trigger + surviving pay | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| A4 | Carriage | carriage event / obligation (seller side for C/D rules) | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ |
| A5 | Insurance | seller insurance obligation (CIF/CIP); level = attribute only | — | — | — | ◐ | — | — | — | — | — | — | ◐ |
| A6 | Delivery / transport document | `BillOfLading` asset + issuance event + `oProvideDocuments` | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A7 | Export/import clearance | `oExportClearance` obligation | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A8 | Checking / packaging / marking | asset attributes / constraints | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| A9 | Allocation of costs | **no cost algebra**; per-stage data / payment obligations | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| A10 | Notices | temporal predicates; "sufficient" lost | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |

## Buyer obligations (B1–B10)

| Art. | Obligation | Device in SymboleoAC | EXW | FCA | CPT | CIP | DAP | DPU | DDP | FAS | FOB | CFR | CIF |
|------|-----------|----------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| B1 | General obligations (pay the price) | `oPay` (surviving) obligation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B2 | Taking delivery | `oTakeDelivery` obligation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B3 | Transfer of risks | see A3; buyer bears risk after delivery point | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| B4 | Carriage | buyer contracts carriage (F-rules) via nomination | ◐ | ✅ | — | — | — | — | — | ✅ | ✅ | — | — |
| B5 | Insurance | buyer insurance (or none) | — | — | — | — | — | — | — | — | — | — | — |
| B6 | Proof of delivery | accept documents; event | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| B7 | Export/import clearance | buyer import clearance obligation | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | — | ◐ | ◐ | ◐ | ◐ |
| B8 | Inspection of goods | inspection event / obligation | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| B9 | Allocation of costs | see A9 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| B10 | Notices | vessel nomination + notice (`oNominateVessel`) | ◐ | ✅ | ◐ | ◐ | ◐ | ◐ | ◐ | ✅ | ✅ | ◐ | ◐ |

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
- **Sea vs any-mode** (FCA/CPT/CIP mirror FAS/CFR/CIF) — the family axis is
  *orthogonal* to the F/C axis, so coverage patterns repeat across it: FCA has
  the same column as the F-terms FAS/FOB, CPT the same as CFR, CIP the same as
  CIF. Only the **vocabulary/device** changes — sea rules name a `vessel` /
  `port` / on-board-or-alongside delivery and a **bill of lading**; any-mode
  rules name a `carrier` / `place` / handover-to-the-(first-)carrier delivery
  and a generic **transport document** (a proof-of-delivery `DocumentsProvided`
  event, no `BillOfLading`). CIP raises insurance to **ICC (A)** vs CIF's ICC (C)
  — a data-only difference (`insuranceCover`). This orthogonality is itself a
  finding: SymboleoAC expresses the normative structure identically regardless of
  transport mode; the mode shows up only as naming, never as different norms.
- **D-terms** (DAP/DPU/DDP) — the seller carries to destination and bears **both**
  risk and cost there, so — unlike C-terms — the risk and cost points **coincide**
  (`oDeliver` is at the destination place, not the origin). Modelled as a `D` term
  type: seller carriage (`oContractCarriage`) + delivery-at-destination, buyer
  takes over there. **DPU** is the only rule where the seller *unloads*
  (`UnloadedAtDestination` delivery event). **DDP** is the maximum-seller term —
  it alone adds a seller **import**-clearance obligation (`oImportClearance` +
  `pTerminateNoImportClearance`), which flips **B7 to —** (the buyer has no
  clearance duty). So across the whole B4/A4 and B7/A7 rows you can read the
  carriage- and clearance-responsibility gradient from EXW → F → C → D → DDP.
- **EXW** — the coverage *floor* and the minimum seller obligation. The seller only
  makes the goods available at its premises (`GoodsMadeAvailable`, `oDeliver`); the
  buyer bears everything onward, **including export clearance**. So EXW is the only
  column with **A4/A5/A6/A7 all = —** (no seller carriage, insurance, document, or
  clearance norms). This is a useful boundary case for the paper: it shows the
  normative surface SymboleoAC needs when almost all duties sit outside the seller —
  and that the buyer-side duties EXW *does* impose (arrange carriage, clear export,
  give collection notice) are exactly the ones that fall to **◐**, since they are
  the counterparty's and not modelled as first-class norms here.
