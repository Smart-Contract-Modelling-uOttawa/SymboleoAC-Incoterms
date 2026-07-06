# Coverage matrix — Incoterms 2020 articles × SymboleoAC

Legend: **✅** modelled · **◐** partially modelled / approximated · **⬜**
expressible in SymboleoAC but not (yet) modelled · **❌** not natively
expressible (language limit) · **—** the ICC text imposes no obligation for
this rule.

The ⬜/❌ split separates *modelling choices* from *language limits* — a cell is
❌ only when SymboleoAC lacks the concept (see `icc-gap-analysis.md` for the
audit against the full ICC text that motivated this distinction).

Columns are the 11 rules. **All 11 columns are filled** — every `specs/*.symboleo`
is generated and compiles 0 errors / 0 warnings. The single shared "Device" column
names the *representative* device; where a rule models an article differently (e.g.
FAS/any-mode proof-of-delivery vs a bill of lading), see the cross-cutting notes.

## Seller obligations (A1–A10)

| Art. | Obligation | Device in SymboleoAC | EXW | FCA | CPT | CIP | DAP | DPU | DDP | FAS | FOB | CFR | CIF |
|------|-----------|----------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A1 | General obligations (goods + invoice conform) | precondition / asset attributes | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| A2 | Delivery (delivery point) | `oDeliver` obligation; delivery event; **string-sale disjunct** (`or WhappensBefore(procuredSoDelivered, …)`) in all 10 non-EXW rules | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A3 | Transfer of risks | **no first-class risk incidence**; but the *exception logic* is modelled: delivery trigger + surviving pay, plus the B3 premature-transfer limbs via `oFailureCosts` (see B3) | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| A4 | Carriage | carriage event / obligation (seller side for C/D rules); E/F transport-info duty via the assistance channel; optional seller-carriage ("if agreed") and the security-compliance duty still unmodelled | ◐ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | ◐ | ✅ | ✅ |
| A5 | Insurance | seller insurance obligation (CIF/CIP, level = attribute only); insurance-info duty of the other rules via the assistance channel | ◐ | ◐ | ◐ | ◐ | — | — | — | ◐ | ◐ | ◐ | ◐ |
| A6 | Delivery / transport document | FOB/CFR/CIF: `BillOfLading` + issuance + `oProvideDocuments`; others: `DocumentsProvided` proof; **FCA adds the optional on-board-B/L mechanism** (agree → instruct → issue → forward). C-rules' document-content requirements (dated within shipment period, negotiable ⇒ full set, sale-in-transit) unmodelled | — | ✅ | ◐ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | ◐ |
| A7 | Export/import clearance | `oExportClearance` obligation; EXW's assistance-only A7 via the assistance channel | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A8 | Checking / packaging / marking | **not yet modelled** — expressible as a packaging/marking obligation ordered before delivery | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| A9 | Allocation of costs | **no cost algebra** for the 13-stage split (data only); but the *behavioural* cost heads are now norms: assistance-reimbursement legs (`oReimburse*Assist`) and the B9(d) failure heads (`oFailureCosts`) | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| A10 | Notices | **not yet modelled** — expressible as notice events + obligations (FCA/FAS/FOB even owe a *dual* delivered-or-failed notice) | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

## Buyer obligations (B1–B10)

| Art. | Obligation | Device in SymboleoAC | EXW | FCA | CPT | CIP | DAP | DPU | DDP | FAS | FOB | CFR | CIF |
|------|-----------|----------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| B1 | General obligations (pay the price) | `oPay` (surviving) obligation — *presence* ✅; price/timing content comes from the sale contract, and the trigger is conditional on delivery+documents (see notes) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B2 | Taking delivery | `oTakeDelivery` obligation (C-rules' second duty — *receive from the carrier at destination* — not separately modelled) | ✅ | ✅ | ◐ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | ◐ |
| B3 | Transfer of risks | **premature-transfer limbs modelled** (`b3_triggers` → surviving `oFailureCosts`, guarded by `Happens(goodsIdentified)`): nomination failure + vessel/carrier failure (F-terms), B7-clearance failure (DAP/DPU), take-delivery failure (EXW). B10-notice limbs of EXW/C-rules and DDP's assistance limb unmodelled (no notice obligation yet); risk *incidence* stays a language gap | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| B4 | Carriage | buyer contracts carriage (F-rules) via nomination | ◐ | ✅ | — | — | — | — | — | ✅ | ✅ | — | — |
| B5 | Insurance | no buyer insurance *obligation*; the CIP/CIF additional-cover info and DAP/DPU/DDP insurance-info duties via the to-seller assistance channel | — | — | — | ◐ | ◐ | ◐ | ◐ | — | — | — | ◐ |
| B6 | Proof of delivery | document events exist; **FCA's B6 instruct-the-carrier limb modelled** (`oInstructCarrierBL`); buyer *acceptance/rejection* (and EXW's buyer-provided evidence) unmodelled | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| B7 | Export/import clearance | **DAP/DPU: first-class buyer obligation** (`oImportClearanceBuyer` — its violation is the B3(a) trigger); B7(a)/DDP assistance limbs via the to-seller channel; the buyer's own transit/import clearance duty in E/F/C rules (incl. EXW's buyer *export* clearance) still unmodelled | ⬜ | ◐ | ◐ | ◐ | ✅ | ✅ | ◐ | ◐ | ◐ | ◐ | ◐ |
| B8 | Checking / packaging / marking | Incoterms 2020 B8 imposes **no buyer obligation** in any rule ("Inspection" was the 2010 numbering) | — | — | — | — | — | — | — | — | — | — | — |
| B9 | Allocation of costs | see A9; the B9(d) failure heads are **modelled** as the surviving `oFailureCosts` for the six rules with a modelled trigger (see B3) | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| B10 | Notices | vessel/carrier nomination event models the notice; notified *content* (buyer-selected date, security requirements, FCA's mode/point) partial | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |

## Cross-cutting findings (running list)

- **2026-07-05 audit against the full ICC publication** (`icc-gap-analysis.md`):
  the matrix was corrected — B8 had used the Incoterms *2010* numbering
  ("Inspection of goods"); B7/A8/A10 cells cited devices absent from the specs
  (now ⬜); several "—" cells contradicted the official text (EXW A7, DDP B7,
  B5 for CIP/CIF/DAP/DPU/DDP, A4/A5 information duties) — the ICC's
  request-triggered *assistance at the requester's risk and cost* pattern
  appears in A4/A5/A6/A7(b)/B5/B7(a) across the corpus. B1's ✅ is for the
  obligation's *presence*: the ICC rules deliberately exclude payment
  time/place/method/currency (they come from the sale contract), and `oPay`
  triggers only on delivery+documents — a buyer whose own failure prevents
  delivery escapes `oPay`, whereas the official B3/B9 provisos make it bear
  risk and additional costs from the agreed date (see the failure-proviso
  finding below).
- **2026-07-05 Wave 1 (post-audit modelling).** Four ICC features moved from
  gap to device, each CI-tested end-to-end (118 scenario/structural tests):
  1. *String sales* — `ProcuredSoDelivered` as a genuine alternative-performance
     disjunct in A2 and in everything keyed on delivery (10 rules).
  2. *B3/B9(d) failure provisos* — the premature risk/cost transfer modelled as
     a **surviving** obligation `oFailureCosts` (trigger: per-rule `b3_triggers`
     — nomination violated, `VesselFailedToLoad`/`CarrierFailedToTakeCharge`
     third-party events, DAP/DPU's `oImportClearanceBuyer` violated, EXW's
     take-delivery violated; antecedent: the ICC "goods clearly identified"
     proviso). Surviving is semantically deliberate: the failure costs outlive
     the termination the failure itself causes — the same device as the
     surviving payment that structurally encodes risk transfer. It is also
     *operationally forced*: the js-core runtime unsuccessfully terminates the
     whole contract on any obligation violation and its termination sweep
     spares only surviving obligations (a runtime-semantics finding worth
     reporting: violation-triggered reparations must be surviving norms).
  3. *Assistance/reimbursement* — one request-triggered channel per direction
     (`oAssistBuyer`/`oAssistSeller` + `oReimburse*Assist`), topics recorded in
     the yaml `assistance` key; covers the "-at the requester's risk and cost"
     duties of A4/A5/A6/A7(b)/B5/B7(a) in consolidated (◐) form.
  4. *FCA on-board B/L* (the 2020 signature change) — dormant-until-agreed
     multi-party mechanism with the carrier as a genuine third party and two
     AC-policy grants; `pResumeDelivery` and with it **all 38 power instances**
     are now created in tests (the suspend→resume cycle completes to
     SuccessfulTermination).
- **Risk (A3/B3)** is the central limitation — SymboleoAC has no risk primitive.
  Modelled structurally (delivery triggers payment; payment survives), and the
  B3 *exception logic* is now expressible/expressed (see above); what remains
  inexpressible is risk *incidence* itself ("who bears loss if the goods are
  damaged at time t"). Candidate language extension for the Discussion section.
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
  buyer bears everything onward, **including export clearance**. EXW remains the
  only column with **A6 = —** and no string-sale limb, and after Wave 1 its
  A4/A5/A7 are ◐ *solely* via the seller's assistance channel — i.e. the ICC text
  itself gives the EXW seller nothing beyond delivery + assistance, which the
  formalization now mirrors exactly. The buyer-side duties EXW imposes (arrange
  carriage, clear export, give collection notice) remain the ◐/⬜ cells, since
  they are the counterparty's and not modelled as first-class norms here — except
  the B9(d) failure head, which is modelled (`oFailureCosts` on take-delivery
  failure).
