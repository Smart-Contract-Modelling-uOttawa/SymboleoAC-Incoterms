# SymboleoAC improvement catalogue — evidence from the Incoterms 2020 corpus

An LLM-assisted assessment of the SymboleoAC **ontology, language, compiler,
runtime, and tooling**, grounded in three modelling waves over the 11 Incoterms
2020 rules (this repo). Every item cites the concrete evidence that produced it;
none is speculative. The closing section is a prioritized **iteration plan** —
one turn of the co-evolution loop between the language stack and the contract
corpus (the KONTEX story: the corpus is both the *consumer* of the stack and its
*regression benchmark*).

Layers, as deployed:
`ontology (Symboleo-JS-Core/ontology: Symboleo.ecore + ontology.ump)` →
`grammar + compiler (SymboleoAC2SC, Xtext)` → `runtime (symboleoac-js-core)` →
`tooling (SymboleoAC-Web IDE + bridge, Application-API, Fabric test network)`.

Status codes: **filed** (upstream issue exists) · **patched** (worked around in
this repo) · **proposed** (new here) · **verified-works** (positive finding —
capability confirmed, documentation should say so).

---

## 1. Ontology (Symboleo.ecore / ontology.ump)

| ID | Finding / proposal | Evidence from the corpus | Status |
|----|--------------------|--------------------------|--------|
| O1 | **First-class `Risk`**: a transferable, insurable object attached to an `Asset`, transferring at a delivery `Event`. | A3/B3 of all 11 rules is modelled only structurally (surviving payment + `oFailureCosts`); "who bears the loss if the goods are damaged at time *t*" is unstatable. The one systematic ◐ the waves never improved. | proposed |
| O2 | **`Cost` concept + allocation algebra**: typed cost stages, a party-boundary, aggregation. | The 13-stage ICC cost table is carried as YAML data; A9/B9 heads conditioned on *another contract's* terms ("unless for the seller's account under the contract of carriage") are unstatable. | proposed |
| O3 | **`Document` concept**: evidence/title/negotiability/transferability as ontology citizens, not ad-hoc events+attributes. | A6 needed `BillOfLading` (asset) + issuance/tender/forward events + `negotiable`/`originalsCount`/`conforming` Env attributes spread across three constructs; *document of title* and sale-in-transit-by-transfer remain inexpressible. | proposed |
| O4 | **Lift access control into the ontology.** The ecore/ump model has *no* AC concepts — `ACPolicy`/`Grant`/read/write/`dept` exist only in the grammar and runtime. Align with RBAC (roles ↔ permissions ↔ resources) and make `dept` (or a general attribute set) part of `Role`. | The on-chain deployment showed AC is a *load-bearing* differentiator (authenticate + per-event grants enforced per transaction), yet the conceptual model cannot even represent it; the `dept` requirement had to be discovered empirically (issue SymboleoAC2SC#1). | proposed |
| O5 | **Party/Role/third-party alignment.** The ontology has `Party` (with `performerOf`/`liableOf`/`rightHolder`) distinct from `Role`; the surface language exposes only role instances, plus a `thirdParty` keyword the ontology lacks. A *third-party beneficiary* concept is missing entirely. | The FOB/FCA carrier is grammar-`thirdParty` with no ontology counterpart; CIP/CIF's "the buyer may claim directly from the insurer" (a right against a non-party) is a defensible ❌ today. `rightHolder` looks like the natural hook. | proposed |
| O6 | **Expose sub-contracts in the surface language.** `Contract.parentContract/subContracts` exists in the ontology with *no grammar counterpart*. | The ICC text repeatedly conditions on the carriage contract's terms; the "network of contracts" (carriage, insurance, L/C) is the domain's structure. The concept is already modelled — only the syntax is missing. | proposed |
| O7 | **Make the reparation pattern explicit.** `Obligation.surviving` is a bare Boolean; nothing says *violation-triggered reparations must be surviving to survive the violation they respond to*. Consider a `Reparation` specialization or a well-formedness rule. | `oFailureCosts` (B9(d)) was stillborn as a regular obligation — created and instantly swept by the violation-triggered contract termination; moving it to Surviving Obligations was both the fix and the semantically right reading. Only execution revealed this. | proposed |
| O8 | **Operations on `TimePoint`/`TimeInterval`.** Both are contentless classes; there is no event-time arithmetic. | DDP's B7-assistance B3 limb needs "within *N* days of the request" — a deadline relative to an event occurrence — inexpressible; only `Date.add` over contract parameters exists. | proposed |
| O9 | **Contract state machine: codegen deviates from the ontology.** In ontology.ump, a contract reaches `UnsuccessfulTermination` only via `terminated` (a power's exercise). The generated runtime unsuccessfully terminates the whole contract *the moment any obligation is violated*, killing the remedial powers the violation just created. | Filed as SymboleoAC2SC#2 with reproduction; forced the surviving-reparation workaround (O7) and reshaped the suspend/resume test design. The ontology is right; the codegen should follow it (or make the policy configurable). | filed |
| O10 | **Obligation state machine: antecedent bypassed at creation.** Ontology: `triggeredConditional → Create --activated--> InEffect`. Codegen: `trigerredUnconditional()` is called for every new instance, so an obligation with an unsatisfied antecedent is already InEffect. | `oFailureCosts`' goods-identification proviso and `oAdditionalCover`'s information precondition are enforced only by a separate activate-listener; firing the antecedent event *before* creation works by accident of ordering. | proposed |

## 2. Language / grammar

| ID | Finding / proposal | Evidence | Status |
|----|--------------------|----------|--------|
| L1 | **Conditional/default expressions** (`if-then-else` or a coalesce over terms), esp. for deadlines. | The ICC B10→A2 cascade — "the buyer-selected date governs; otherwise the end of the agreed period" — cannot be written: an `or` of two `WhappensBefore` *loosens* (either bound suffices) instead of *overriding*. We left it unmodelled rather than model it wrongly. Same shape as every "unless otherwise agreed" default. | proposed |
| L2 | **Ordered enumerations / comparable domain values** (e.g. `Enumeration(C < B < A)`). | Insurance cover: amount (110%) and currency are now *checked* constraints, but "at least ICC (C)" is inexpressible — the clause set stays a string. The one item keeping A5 at ◐. | proposed |
| L3 | **Defeasible obligations** ("unless X, in which case discharged"). | A8's two ICC defeaters (unpackaged trade usage; agreed specific packaging) and CIP/CIF's "unless otherwise agreed or customary" are comments, not semantics. | proposed |
| L4 | **Event-relative deadlines** (see O8) — surface form: `Date.add(eventVar, n, days)` where `eventVar`'s occurrence time is meant. | DDP B7-assistance limb; also the natural form for "reimburse within N days of assistance". | proposed |
| L5 | **Module/include mechanism.** | "Shared ontology" across the 11 specs means the generator inlines identical text; 2,000+ spec LOC are ~60% repetition the language cannot factor. | proposed |
| L6 | **Vague-standard annotations** ("sufficient", "customary", "usual route", "in the manner customary at the port") — perhaps a named-standard reference resolvable by an oracle/expert at runtime. | A10/B10's "sufficient notice", A4's carriage-quality terms, FAS/FOB's port-custom manner: all approximated by deadlines or dropped; the qualifier is *lost*, not just weakened. | proposed |
| L7 | **Positive findings to document as supported** (currently absent from any reference doc): `or` in triggers and consequents; arithmetic (`1.1 * price`) and enum/Boolean comparison in propositions; **Boolean contract parameters**; **cross-event attribute references incl. Env dates as deadline points**; **powers targeting surviving obligations** (`Suspended(obligations.oPay)` compiles, and the generated exercise transaction routes to `survivingObligations` correctly — verified end to end in the B6 rejection cycle, test-covered). | Waves 1–3 probe results; the last one replaces a long-standing "unverified, avoid" note in this repo's CLAUDE.md. | verified-works |

## 3. Compiler / code generator (SymboleoAC2SC)

| ID | Finding / proposal | Evidence | Status |
|----|--------------------|----------|--------|
| C1 | `createSurvivingObligation_*` references an undeclared `isNewInstance` (crashes every surviving obligation at runtime); a second shape appears when the surviving antecedent is non-trivial. | Patched in `tests/scenarios/generate.mjs` (`patchCodegen`, two patterns); mentioned in issue #2. | patched |
| C2 | **Arithmetic in a consequent** emits a JS `SyntaxError` in the contract class's `LegalSituation` metadata builder (nested, mis-quoted `addConsequentOf` in `rightSide`), while the norm-evaluation condition is generated correctly. The spec compiles 0/0 — only execution catches it. | Filed as SymboleoAC2SC#3; patched in `patchCodegen`. | filed+patched |
| C3 | Roles need a `dept` attribute for the generated `authenticate`; the compiler should add/require it instead of failing opaquely on-chain with "Unauthorized". | Filed as SymboleoAC2SC#1. | filed |
| C4 | **Add a generated-JS self-check** (`node --check` over every emitted file) to the codegen pipeline, so C2-class defects fail the *compile* gate rather than surfacing at deployment. | The 0-error/0-warning gate passed while the generated CIF.js was unparseable. | proposed |
| C5 | `getState` returns prose, `getLegalPositionStateAndTime` returns JSON — unify on JSON for machine consumption. | On-chain verification had to parse a human-oriented string. | proposed |
| C6 | Codegen should follow the ontology state machines (see O9/O10) or expose the violation policy as a generation option. | SymboleoAC2SC#2. | filed |

## 4. Runtime (symboleoac-js-core)

| ID | Finding / proposal | Evidence | Status |
|----|--------------------|----------|--------|
| R1 | **Interval-based `HappensWithin`.** The implementation is state-based (`event.hasHappened() && object.isSuspended()`): an event that happened *before* a suspension counts as happening *within* it. | The pResumeDelivery cycle relies on a re-dispatch of an old nomination during suspension — semantically a late nomination, operationally a replay. `Situation.time: TimeInterval` exists in the ontology; the runtime ignores it. | proposed |
| R2 | **Subscription model is object-reference-based**; listeners bound at map-build time miss norms created later, so every emit requires rebuilding the event map. | The harness re-inits before every fire (as the Fabric wrapper accidentally does per transaction); a name-based registry would remove the trap for any long-lived (non-Fabric) host. | proposed |
| R3 | **Event occurrences are single-shot.** `happen()` re-stamps the same object; there is no occurrence history. | A re-tendered document (B6 conforming re-tender) is really a *second occurrence* of `DocumentsProvided`; we model it by attribute mutation. Recurring obligations (periodic payments) would hit this wall immediately. | proposed |
| R4 | Violation → eager whole-contract termination (runtime side of O9/C6). | SymboleoAC2SC#2. | filed |

## 5. Tooling (Web IDE, bridge, Application-API, test network)

| ID | Finding / proposal | Evidence | Status |
|----|--------------------|----------|--------|
| T1 | **Role-identity provisioning should be first-class.** The Application-API hard-codes a `fabric-network-2.2.2` layout and macOS paths; we bypassed it with direct `fabric-ca-client` enrollment (attrs as `ecert`, NodeOU config copy) — now documented in `deploy/README.md` §5. | Full authorized on-chain happy path (11 transactions, 3 identities) achieved CLI-only. | proposed |
| T2 | IDE/bridge lints: warn on roles without `dept` (AC will reject on-chain), and surface the C4 generated-JS check in the Web IDE's Generate flow. | Both failure modes are invisible until deployment today. | proposed |
| T3 | Test network `network.sh` hard-codes `bin-macos`; Fabric 2.2's `fabric-nodeenv` is Node 12 (crashes on modern syntax). Fix/retag upstream. | deploy/README.md fixes 1 and 4. | proposed |

---

## 6. Iteration plan (one co-evolution turn, reportable in the KONTEX paper)

Ordered by leverage-per-effort; each phase ends by **re-running this corpus**
(compile gate → 147 scenario/structural tests → Fabric redeploy) as the
regression benchmark, and re-scoring the coverage matrix. Expected matrix
movement is stated per phase — that is the measurable "one iteration" claim.

**Phase 0 — hygiene (days; SymboleoAC2SC + test network).**
Fix C1/C2 in the code generator (retiring `patchCodegen`), add the C4
generated-JS self-check, C3 dept handling, T3 network fixes.
*Corpus effect:* none on the matrix; removes two workaround layers and makes
the compile gate trustworthy.

**Phase 1 — runtime semantics (weeks; js-core + codegen).**
R4/O9: violation defers whole-contract termination when a remedial power or
violation-triggered norm exists (or a per-contract policy flag); O10/R-side:
honour antecedents at creation (Create until activated); R1 interval-based
`HappensWithin`.
*Corpus effect:* `oFailureCosts` could be a regular obligation again (though
surviving remains the better legal reading — the paper can discuss both);
breach scenarios can continue past a violation, so suspend→resume after a
late nomination becomes semantically clean rather than replay-based.

**Phase 2 — small language increments (weeks; grammar + codegen).**
L2 ordered enumerations; L4/O8 event-relative deadlines; L1 conditional
deadline expressions.
*Corpus effect:* A5 ◐→✅ for CIP/CIF ("at least ICC (C)" as a constraint);
B10→A2 dynamic deadline modelled faithfully (upgrading A2/B10 fidelity for all
F-terms); DDP's last unmodelled B3 limb closes — every premature-transfer limb
of the standard would then be first-class.

**Phase 3 — ontology alignment (months; ontology + grammar).**
O4 RBAC concepts into the ontology (the SymboleoAC extension becomes
conceptually grounded, not just implemented); O7 `Reparation`; O5 third-party
beneficiary via `rightHolder`; O6 surface syntax for sub-contract references;
L5 modules.
*Corpus effect:* the insurer direct-claim (A5) and the
cost-heads-conditioned-on-the-carriage-contract (A9/B9) become expressible;
the generator's inlined "shared ontology" becomes a real module; spec LOC
drops substantially.

**Phase 4 — research extensions (the JURIX agenda).**
O1 risk, O2 cost algebra, L3 defeasibility, L6 vague standards.
*Corpus effect:* the remaining ◐ rows (A3/B3, A9/B9, the defeaters, the
qualifiers) — the honest frontier.

**Benchmark protocol per phase:** regenerate the 11 specs → 0/0 compile →
147 tests green → power-instance census (currently 48/48) → coverage matrix
re-score (the diff is the phase's measured outcome) → FOB Fabric redeploy for
phases touching codegen/runtime.
