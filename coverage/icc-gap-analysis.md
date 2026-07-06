# Gap analysis vs. the official ICC Incoterms 2020 publication

Source: the full ICC text ("Incoterms 2020 — ICC rules for the use of domestic and
international trade terms", 195 pp.; local copy at `paper/refs/Incoterms2020-ICC-full.pdf`,
not committed — ICC copyright). Analyzed 2026-07-05 against `specs/*.symboleo`,
`generator/incoterms.data.yaml`, `coverage/coverage-matrix.md`, and `paper/main.tex`.

This document records (1) factual errors to fix, (2) modelling gaps ranked by value,
(3) paper-only (non-normative) material. Line references "ICC p.N" are pages of the
publication.

---

## 1. Factual errors / audit-vulnerable claims (fix before submission)

1. **Coverage-matrix B8 row is Incoterms *2010* numbering.** It is titled
   "Inspection of goods" and scored ◐×11. In Incoterms 2020, B8 is
   *checking/packaging/marking* and says **the buyer has no obligation** in all 11
   rules — the correct row is "—"×11 (trivially satisfied). A8 (seller: pay
   checking operations; package and mark appropriately, with two "unless"
   defeaters) is currently unmodelled, so its ◐ via "asset attributes /
   constraints" names a device that exists in no spec.
2. **Matrix cells name devices that don't exist in any spec:**
   - B7 ◐×9 claims a "buyer import clearance obligation" — no spec has the buyer
     as debtor of *any* clearance norm (grep-verified).
   - A10 ◐ via "temporal predicates" — no A10 seller-notice event or obligation
     exists anywhere.
   - A8 ◐ via "asset attributes" — `Goods` has only description/quantity/owner.
3. **Matrix "—" cells that contradict the official text** ("—" must mean *the ICC
   text imposes no obligation*): EXW A7 (seller *assistance* duty exists), DDP B7
   (buyer assistance duty exists), B5 for CIP/CIF (buyer info duty for additional
   cover) and DAP/DPU/DDP (buyer must supply insurance info at seller's
   request/risk/cost), A4/A5 for EXW/F-rules/CPT/CFR (request-triggered
   information duties exist).
4. **Paper claim "35 of the 38 powers are created on a breach path" is wrong.**
   Powers are trigger-created; per the actual scenario suite the distinct
   (rule, power) instances created ≈ 25/38: never created are the 3
   `pResumeDelivery`, plus `pTerminateNoCarriage` for 6 of 7 carriage rules (only
   CPT drives that breach), plus `pTerminateByBuyer` for rules whose seller-breach
   test violates a different obligation. Either extend the suite (one breach per
   power per rule) or restate as power *types*.
5. **Abstract/§5 "cannot express" vs. matrix ◐**: the ❌ symbol is defined in both
   legends but used in zero cells, while the abstract promises a three-way
   distinction. Decide: either introduce genuine ❌ cells (candidates: risk
   *incidence* primitive, document-of-title semantics, third-party-beneficiary
   direct-claim on the insurer) or soften the abstract to "only indirectly".
6. Minor: generator docstring says term axis is "F vs C" (it is E/F/C/D);
   `oNominate*` comment says "B7/B10" (should be B4/B10); yaml
   `insurance_cover: ICC_A_110pct` never reaches runtime in that form (tests pass
   free-form strings) — nothing pins CIF to ICC(C) even as data.

## 2. Modelling gaps, ranked (generator + specs + yaml)

Each of these is expressible in SymboleoAC today; adding them is a modelling
decision, not a language extension. The yaml schema needs new keys before the
specs can absorb them in a generated, structurally-parallel way (ground rule 2):
suggested keys `b3_triggers`, `transit_clearance`, `assistance`,
`failure_cost_heads`, `security`, `notice_content`.

1. **B3 premature-risk-transfer provisos + their B9(d) cost twins** — the rules'
   only real "consequence" logic and the richest deontic structure in the corpus.
   Trigger sets differ per rule: B10-notice failure (all); FCA: buyer fails to
   nominate carrier OR nominated carrier fails to take charge; FAS/FOB: vessel
   fails to arrive / fails to take the goods / **closes for cargo earlier** than
   notified; DAP/DPU/DDP: buyer's B7-failure limb ("all *resulting* risks").
   All guarded by "provided the goods have been clearly identified as the
   contract goods" (an Env boolean). Modellable as powers/triggered obligations:
   e.g. `Violated(oNominate) or Happens(vesselFailedToLoad) → O(buyer, seller, …,
   additional costs)` + making `oPay` (risk proxy) trigger from the agreed
   date. **This flips the paper's A3/B3 story**: the *exception logic* IS
   expressible; only the risk-incidence primitive is not. Requires new
   third-party failure event types (carrier/vessel failure) — natural Env events.
2. **The request/risk/cost assistance pattern** (A4/A5/A6/A7(b), B5, B7(a)) —
   ~6 conditional obligations per rule, ~60 across the corpus, each with an
   A9/B9 reimbursement leg. One reusable template pair
   (`Happens(request) → O(party, other, …, provide)` + reimbursement obligation)
   closes the largest count of gaps in a single generator change.
3. **"Procure goods so delivered" (string sales)** — an alternative fulfilment
   disjunct in A2 of all 10 non-EXW rules, emphasized by ICC for the maritime
   terms. One-disjunct fix: `… or Happens(procuredSoDelivered)`. A2 ✅ currently
   overclaims without it.
4. **FCA on-board bill of lading mechanism (A6/B6)** — the signature 2020
   drafting change and an ideal multi-party SymboleoAC showcase: contract flag →
   buyer must instruct its carrier (at buyer's cost/risk) to issue an on-board
   B/L to the seller → carrier issuance event (may not accede — external) →
   seller must forward the document to the buyer. Also a natural AC-policy
   exhibit (carrier writes, both parties read).
5. **Buyer-side clearance obligations + transit as a third clearance category.**
   No spec makes the buyer debtor of any clearance norm. Official split:
   EXW — buyer does even export; F/C rules — buyer does transit+import;
   DAP/DPU — seller does export+transit (transit is the DAP/DPU vs DDP
   differentiator, unrepresentable in the current yaml); DDP — seller does all
   three. All prefixed "where applicable" (an `Env clearanceApplicable` guard).
6. **Transport-security requirements (2020 innovation) — zero footprint.** A
   compliance obligation in every A4 except EXW (scope differs: "up to delivery"
   for E/F vs "to destination" for C/D), a security-clearance head in A7/B7,
   notified content in B10 (FCA/FAS/FOB), cost heads in A9/B9. One
   `securityRequirements` thread through the generator covers a theme reviewers
   will expect a 2020-specific paper to mention.
7. **A8 checking/packaging/marking** — uniform across all 11 rules and cheap: a
   `PackagedAndMarked` event + seller obligation `ShappensBefore(…, delivery)`,
   with the two "unless" defeaters recorded as data. Makes the current ◐ true.
8. **A10 seller notices** — load-bearing and absent: EXW B2 conditions taking
   delivery on the A10 notice; FCA/FAS/FOB A10 is a *dual* notice (delivered OR
   carrier/vessel failed to take the goods — presupposes the failure events of
   item 1); C-rules require a post-delivery notification (event-triggered, not
   deadline-based).
9. **Dynamic delivery deadline from B10 notice** — the official F-term deadline
   cascade is: agreed date → time notified by buyer → end of agreed period. Specs
   hard-code `Date.add(effDate, deliveryDays)`; the nomination events don't even
   carry the selected date. Also enrich notice content: FCA's four items
   (carrier, time, mode+security, point); FAS/FOB's vessel/loading-point/date/
   security.
10. **Insurance sub-obligations (CIP/CIF A5)** beyond bare existence: amount
    ≥ 110% of price in the contract currency (attribute constraints — expressible
    now), cover span (delivery point → destination), **provide the
    policy/certificate to the buyer** (discrete document obligation), and the
    conditional additional-cover obligation (buyer request + buyer info as
    antecedent, "if procurable" escape — a nested conditional worth showing).
    The buyer's direct-claim entitlement against the insurer is genuinely
    third-party-beneficiary semantics — a defensible ❌.
11. **A6 document-content constraints** — dated within the shipment period (a
    temporal predicate the language *has*), covers the contract goods,
    negotiable ⇒ full set of originals, enable sale in transit (opt-in "if agreed
    or customary" for CPT/CIP vs opt-out "unless otherwise agreed" for CFR/CIF —
    a real inter-rule differential the generator flattens). B6 acceptance
    "if in conformity with the contract" implies a buyer *rejection power* —
    unmodelled. EXW B6 flips direction (buyer provides evidence of taking
    delivery). Note: matrix implies CPT/CIP have the BillOfLading device — they
    don't (only FOB/CFR/CIF do).
12. **FCA's two delivery modes** (seller's premises: loaded on buyer's transport
    vs. other place: on seller's transport ready for unloading) collapse into one
    event; the risk-relevant distinction (who bears loading/unloading) is lost.
    Similarly: DPU's unload-then-deliver sequencing (only rule where seller
    unloads) could be two ordered events; DAP delivers "ready for unloading".
13. **A1 commercial invoice** — a concrete document obligation (event parallel to
    `DocumentsProvided`) absent from all 11; also "any other evidence of
    conformity required by the contract".
14. **Unloading-cost non-recovery rule** (C/D rules: if seller's carriage
    contract included unloading at destination, seller may not recover those
    costs "unless otherwise agreed") — a *prohibition*, interesting as a
    constraint/no-power; plus the "only if for the seller's account under the
    contract of carriage" heads: conditions referencing *another contract's*
    terms — a genuine expressiveness finding to name in the matrix.

## 3. Paper-only material (non-normative, for §2/§5/§7)

- **The exclusion list (ICC Intro)**: the rules deliberately do NOT deal with
  transfer of property/title, payment time/place/method/currency, remedies for
  breach, force majeure, dispute resolution. Consequence for the paper: the
  SymboleoAC breach powers, payment deadlines, and termination logic are
  *extensions beyond* Incoterms (contract-of-sale material), not coverage of it.
  This reframing should be explicit — it also explains why B1 ✅ needs a footnote
  (price/timing come from the sale contract, not the rule).
- **Named-place semantics per family**: non-C rules — named place = delivery =
  risk point; D rules — delivery AND destination coincide; C rules — named place
  is destination ONLY, never the delivery point (two place parameters needed).
  A structural invariant worth stating (and asserting differentially).
- **A2 delivery as the single pivot** for risk (A3) and costs (A9) — matches the
  specs' design; state it as an invariant.
- **First-carrier default + residual A4 liability (C rules)**: with no agreed
  point, risk passes on handover to the *first* carrier; buyer's protection is
  the seller's surviving A4 duty (carriage contract must reach the destination) —
  parallels the payment-survives-termination encoding.
- **FCA/FOB: the relevant carrier is the buyer's nominee** — handover to the
  seller's own haulier/feeder does not transfer risk; the delivery event must be
  typed as handover-to-buyer's-nominee.
- **VGM (SOLAS container weighing)**: the ICC Drafting Group *deliberately*
  declined to allocate it — a documented, intentional gap in the source standard
  itself; strengthens the coverage-yardstick narrative.
- **EXW loading-risk ambiguity**: the ICC notes admit that when the seller loads
  in fact, risk incidence is arguable — source-text indeterminacy a formal model
  must resolve by choice; excellent discussion material.
- **Custom/usualness standards** ("usual terms", "usual route", "customary
  manner", "in the manner customary at the port", "sufficient notice") — the
  known vague-qualifier limit; now with a fuller catalogue of instances.
- **Electronic-document parity (A1, 2020's generalized clause)** — a free win for
  the smart-contract/Fabric deployment story: the standard itself is
  mode-neutral about document form.
- **Horizontal presentation**: ICC 2020 publishes the rules per-article across
  all 11 rules for the first time — a direct precedent for the generator +
  coverage-matrix approach; cite it as methodological alignment.
- **Network of contracts**: carrier/insurer/bank are not bound by the sale
  contract — frames third parties as environment roles and motivates the
  AC-policy design (and the FCA B/L mechanism as the sale contract *steering*
  the carriage contract).
- **Explanatory notes vs. rules**: the Introduction and Explanatory Notes are
  expressly NOT part of the rules — the coverage matrix should key only on the
  A/B article text (methodological caveat).
- **ICC steering advice** (avoid EXW/DDP extremes, container caveats for
  FAS/FOB, local-insurance caveat for CIP/CIF) — rule-*selection* guidance is
  outside any single contract's formalization; worth one paragraph.

## 4. Wave plan and status

- **Wave 0 (DONE, PR #2):** matrix B8 row fixed; phantom-device cells re-scored
  with the new ⬜ mark; wrong "—" cells fixed; powers claim corrected.
- **Wave 1 (DONE, PR #2):** B3/B9 failure provisos with third-party failure
  events (surviving `oFailureCosts`), assistance/reimbursement pair,
  string-sales disjunct, FCA on-board B/L. Tests 44→118, all 38 powers created.
- **Wave 2 (DONE, PR #3):** A8 packaging (item 7), A10/B10 notices (item 8 —
  incl. the F-terms' dual notice, and the notice-limb B3 triggers that give all
  11 rules `oFailureCosts`), insurance sub-obligations with checked 110%/currency
  constraints (item 10), buyer clearance breadth incl. EXW's full-clearance
  mirror of DDP (item 5), and the security thread (item 6). Tests →130. A third
  upstream codegen defect (arithmetic in consequents breaks the LegalSituation
  metadata builder) patched in the harness.
- **Wave 3 (DONE, PR #4):** A1 commercial invoice ×11; A6 document-content
  constraints for the B/L rules; DPU arrival-before-unloaded-delivery
  sequencing; B6 buyer rejection power suspending the *surviving* payment
  (which verified that powers may target surviving obligations end to end).
  Deliberately unmodelled with the language gap recorded in
  `symboleoac-improvements.md`: the dynamic B10→A2 deadline cascade (needs
  conditional/default expressions), DDP's B7-assistance B3 limb (needs
  event-relative deadlines). Tests →147, 48/48 power instances.
- **Remaining (modelling roadmap, no language obstacle):** FCA's two delivery
  modes as distinct events; per-article (rather than consolidated) assistance
  obligations. **Blocked on language/tooling evolution:** see the improvement
  catalogue + iteration plan in `symboleoac-improvements.md` (the KONTEX
  co-evolution artifact).
