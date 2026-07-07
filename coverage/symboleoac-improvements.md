# SymboleoAC improvement catalogue — evidence from the Incoterms 2020 corpus

An LLM-assisted assessment of the SymboleoAC **ontology, language, compiler,
runtime, and tooling**, grounded in three modelling waves over the 11 Incoterms
2020 rules (this repo). Every item cites the concrete evidence that produced it;
none is speculative. The closing section is a prioritized **iteration plan** —
one turn of the co-evolution loop between the language stack and the contract
corpus (the KONTEX story: the corpus is both the *consumer* of the stack and its
*regression benchmark*).

Layers, as deployed:
`ontology (SymboleoAC-JS-Core/ontology/SymboleoAC.ump — the Symboleo core + the Access Control extension)` →
`grammar + compiler (SymboleoAC2SC, Xtext)` → `runtime (symboleoac-js-core)` →
`tooling (SymboleoAC-Web IDE + bridge, Application-API, Fabric test network)`.

> **Provenance note — itself a finding (O4d).** The first version of this
> assessment analyzed `Symboleo-JS-Core/ontology/ontology.ump`, the *plain
> Symboleo* ontology in the sibling repository, and wrongly concluded that the
> ontology had no access-control concepts. The authoritative model,
> `SymboleoAC-JS-Core/ontology/SymboleoAC.ump`, embeds a copy of the core
> ontology and extends it with a full AC layer (`Resource`, `Policy`, `Rule`
> with `Grant/Revoke` × `read/write/all/transfer`, `Operation`, `Attribute`,
> `DataTransfer`, `StateTransition`, `AbstractEvent`). The two files share
> their Contract/Obligation/Power state machines verbatim — so every
> state-machine finding below holds for both — but they are related by
> copy-and-extend, not module reuse: exactly the divergence hazard that misled
> the assessment, and that O4d proposes to fix.

Status codes: **filed** (upstream issue exists) · **patched** (worked around in
this repo) · **proposed** (new here) · **verified-works** (positive finding —
capability confirmed, documentation should say so).

---

## 1. Ontology (SymboleoAC.ump)

| ID | Finding / proposal | Evidence from the corpus | Status |
|----|--------------------|--------------------------|--------|
| O1 | **First-class `Risk`**: a transferable, insurable object attached to an `Asset`, transferring at a delivery `Event`. | A3/B3 of all 11 rules is modelled only structurally (surviving payment + `oFailureCosts`); "who bears the loss if the goods are damaged at time *t*" is unstatable. The one systematic ◐ the waves never improved. | proposed |
| O2 | **`Cost` concept + allocation algebra**: typed cost stages, a party-boundary, aggregation. | The 13-stage ICC cost table is carried as YAML data; A9/B9 heads conditioned on *another contract's* terms ("unless for the seller's account under the contract of carriage") are unstatable. | proposed |
| O3 | **`Document` concept**: evidence/title/negotiability as ontology citizens, not ad-hoc events+attributes. | A6 needed `BillOfLading` (asset) + issuance/tender/forward events + `negotiable`/`originalsCount`/`conforming` Env attributes spread across three constructs. *Endorsability* turned out to be expressible with the AC ontology's own `transfer` action (see O4b) — the specs now grant the buyer `transfer` rights over the B/L — but a document-of-title *semantics* (holder-of-the-document = right-to-the-goods) still has no home. | proposed |
| O4a | **Conceptualize the identity→role authentication mapping.** In SymboleoAC.ump, `Role` has *no attributes*; the runtime's `authenticate` matches four certificate fields (`HF.name`/`HF.role`/`organization`/`department`) against role data — classic RBAC user-assignment, implemented but not modelled. | The `dept` requirement had to be discovered empirically on-chain ("Unauthorized" with no modelled reason; issue SymboleoAC2SC#1); the CLI enrollment recipe in deploy/README.md §5 encodes knowledge that belongs in the ontology (a `Credential`/assignment concept). | proposed |
| O4b | **Surface and exercise the ontology's full AC vocabulary.** `Rule` supports `Grant/Revoke` × `read/write/all/transfer`; the grammar accepts all of them (probe-verified) — yet the corpus, the group's examples, and the docs only ever use `Grant read/write`. `transfer` is exactly the negotiable-document primitive the trade domain needs; `Revoke` gives negative authorization (e.g. cutting a carrier's access after termination). Document them, give them runtime semantics tests, and add codegen/Fabric transactions that *exercise* a transfer. | Wave-3 probes: `Grant transfer To buyer On billOfLading`, `Revoke read`, `Grant all` all compile 0/0; the B/L rules' ACPolicy now records the buyer's transfer right as the endorsability device (A6). Whether js-core *enforces* transfer/Revoke is untested — the next probe target. | verified-works (grammar) / proposed (runtime) |
| O4c | **Ontology-internal quality pass.** `Operation.preCondition/postCondition` are typed `Condition` — a type declared nowhere in the ump; association names carry typos (`LegalPositionStateEven`, `ruleAccesseor`, `inputAttributs/outputAttributs`). | Direct reading of SymboleoAC.ump. Cosmetic, but this is the conceptual model of record for a journal-published language. | proposed |
| O4d | **Modularize the two ontologies + provenance.** SymboleoAC.ump embeds a copy of the plain-Symboleo ontology rather than importing it; the sibling repo (`Symboleo-JS-Core/ontology`, with the Ecore/EMF model and diagrams) still hosts the old version with no derivation note; the AC extension has **no Ecore/EMF model at all** (ump only), so the published class diagrams show pre-AC Symboleo. | This assessment's own v1 mistake: the stale sibling ontology is the one a reader finds first. Umple supports mixins/traits for exactly this composition. | proposed |
| O5 | **Party/Role/third-party alignment.** The ontology has `Party` (with `performerOf`/`liableOf`/`rightHolder`) distinct from `Role`; the surface language exposes only role instances, plus a `thirdParty` keyword the ontology lacks (the AC extension adds `Event.performer: Role`, aligning event performers, but the third-party notion itself is still grammar-only). A *third-party beneficiary* concept is missing entirely. | The FOB/FCA carrier is grammar-`thirdParty` with no ontology counterpart; CIP/CIF's "the buyer may claim directly from the insurer" (a right against a non-party) is a defensible ❌ today. `rightHolder` looks like the natural hook. | proposed |
| O6 | **Expose sub-contracts in the surface language.** `Contract.parentContract/subContracts` exists in the ontology with *no grammar counterpart*. | The ICC text repeatedly conditions on the carriage contract's terms; the "network of contracts" (carriage, insurance, L/C) is the domain's structure. The concept is already modelled — only the syntax is missing. | proposed |
| O7 | **Make the reparation pattern explicit.** `Obligation.surviving` is a bare Boolean; nothing says *violation-triggered reparations must be surviving to survive the violation they respond to*. Consider a `Reparation` specialization or a well-formedness rule. | `oFailureCosts` (B9(d)) was stillborn as a regular obligation — created and instantly swept by the violation-triggered contract termination; moving it to Surviving Obligations was both the fix and the semantically right reading. Only execution revealed this. | proposed |
| O8 | **Operations on `TimePoint`/`TimeInterval`.** Both are contentless classes; there is no event-time arithmetic. | DDP's B7-assistance B3 limb needs "within *N* days of the request" — a deadline relative to an event occurrence — inexpressible; only `Date.add` over contract parameters exists. | proposed |
| O9 | **Contract state machine: codegen deviates from the ontology.** In SymboleoAC.ump (identically in the core ontology), a contract reaches `UnsuccessfulTermination` only via `terminated` (a power's exercise). The generated runtime unsuccessfully terminates the whole contract *the moment any obligation is violated*, killing the remedial powers the violation just created. | Filed as SymboleoAC2SC#2 with reproduction; forced the surviving-reparation workaround (O7) and reshaped the suspend/resume test design. The ontology is right; the codegen should follow it (or make the policy configurable). | filed |
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
| L7 | **Positive findings to document as supported** (currently absent from any reference doc): `or` in triggers and consequents; arithmetic (`1.1 * price`) and enum/Boolean comparison in propositions; **Boolean contract parameters**; **cross-event attribute references incl. Env dates as deadline points**; **powers targeting surviving obligations** (`Suspended(obligations.oPay)` compiles, and the generated exercise transaction routes to `survivingObligations` correctly — verified end to end in the B6 rejection cycle, test-covered); **the full AC rule vocabulary** — `Grant transfer`, `Revoke`, `Grant all` all parse and compile (see O4b). | Waves 1–3 probe results; the surviving-power one replaces a long-standing "unverified, avoid" note in this repo's CLAUDE.md. | verified-works |

## 3. Compiler / code generator (SymboleoAC2SC)

| ID | Finding / proposal | Evidence | Status |
|----|--------------------|----------|--------|
| C1 | `createSurvivingObligation_*` references an undeclared `isNewInstance` (crashes every surviving obligation at runtime); a second shape appears when the surviving antecedent is non-trivial. | Was patched in `tests/scenarios/generate.mjs` (`patchCodegen`, two patterns); mentioned in issue #2. **Fixed 2026-07-07** in `Symboleo2SC.xtend` (declaration mirrors `createObligation_*`), on the `claude/phase0-codegen-fixes` branches of SymboleoAC-IDE and SymboleoAC-Web; `patchCodegen` retired. | **fixed** (PR pending) |
| C2 | **Arithmetic in a consequent** emits a JS `SyntaxError` in the contract class's `LegalSituation` metadata builder (nested, mis-quoted `addConsequentOf` in `rightSide`), while the norm-evaluation condition is generated correctly. The spec compiles 0/0 — only execution catches it. | Filed as SymboleoAC2SC#3; was patched in `patchCodegen`. **Fixed 2026-07-07**: `generateLegalpositionCondition`'s `PArithmetic` case now emits the operand flat (`left op right`) instead of wrapping it in another `addAC(...)` call — an arithmetic node is an operand of the enclosing comparison, not a condition of its own. Same branches as C1; W8 retired with it. | **fixed** (PR pending) |
| C3 | Roles need a `dept` attribute for the generated `authenticate`; the compiler should add/require it instead of failing opaquely on-chain with "Unauthorized". | Filed as SymboleoAC2SC#1. | filed |
| C4 | **Add a generated-JS self-check** (`node --check` over every emitted file) to the codegen pipeline, so C2-class defects fail the *compile* gate rather than surfacing at deployment. | The 0-error/0-warning gate passed while the generated CIF.js was unparseable. **Implemented 2026-07-07** in `codegen-cli` (SymboleoAC-Web `claude/phase0-codegen-fixes`): failures become ERROR issues (`generated-js-syntax`), non-zero `summary.errors`, exit 1; skipped with a stderr note where `node` is absent (the bridge image ships node). Detection verified live: a jar with C4 but *without* the C2 fix rejected CIF with the exact SyntaxError that previously reached deployment. | **implemented** (PR pending) |
| C5 | `getState` returns prose, `getLegalPositionStateAndTime` returns JSON — unify on JSON for machine consumption. | On-chain verification had to parse a human-oriented string. | proposed |
| C6 | Codegen should follow the ontology state machines (see O9/O10) or expose the violation policy as a generation option. | SymboleoAC2SC#2. | filed |
| C7 | **Extend the Xtext validator with pragmatic well-formedness rules.** The current `SymboleoValidator` (17 active checks) is strong on reference/type consistency but nearly silent on what the codegen, runtime, and blockchain *assume*; two further checks (unique AC-rule names; the permission-giver rule) sit half-written and commented out. See the tiered rule set below. | Five probes against the deployed jar (2026-07-06): an Event with **no `performer`/`controller`** compiles 0/0 and its JS parses, yet every generated trigger transaction dereferences `_controller` for the AC layer — the event is untriggerable on-chain; a domain type `Function` + a variable named `constructor` compile and parse but silently corrupt the contract object (property shadowing); duplicate `Rule1:` names are accepted; a violation-triggered obligation in the *main* section is accepted although the runtime makes it stillborn (the `oFailureCosts` trap). Only the dangling-`obligations.X` probe was correctly rejected (scoping). | proposed |

**C7 — validation rules, tiered for backward compatibility (expert-reviewed
2026-07-07).** The LLM's original 12-rule proposal was reviewed with domain
experts; rule (1) was modified, (6) was promoted to an error, and (4), (5),
(7), (10) were removed — the removal rationales are recorded below because
the review itself is co-evolution data.

*Errors* (structural requirements the generated code already assumes):
(1) every Event type declares a Role-typed `performer`;
(2) no identifier collides with JS/Java reserved words or generated member
names (`constructor`, `state`, `obligations`, `notified`, …);
(3) unique AC-rule names (finish the commented-out check);
(6) every Role type declares the AC-required attributes
(`name`/`org`/`dept`) — SymboleoAC2SC#1 at compile time instead of an
on-chain "Unauthorized".
*Warnings* (semantics traps found empirically in this corpus):
(8) arithmetic in a consequent — until C2 is fixed (pairs with C4).
*(Retired 2026-07-07: C2 is fixed, so W8 has no remaining purpose — an
example of a validator rule whose designed lifetime ends with the defect it
guards; CIF/CIP return to 0-warning.)*
*Lints* (completeness/reachability):
(9) finish the permission-giver check (the `by` role should be owner,
controller, or performer of the granted resource);
(11) dormant norms — a conditional norm whose trigger event appears nowhere
else and has no performer path;
(12) the validator's own TODO list: inheritance cycles, expression cycles.
All are ordinary `@Check(FAST)` methods in one file with an existing tests
module; the single warning tier keeps every published spec compiling.

**IMPLEMENTED 2026-07-07** — [SymboleoAC-IDE#1](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-IDE/pull/1)
(validator + cycle-guarded `Helpers.getBaseType`/`getAttributesOfRegularType`,
promoted E12a to an error because a cycle previously crashed the compiler) and
[SymboleoAC-Web#6](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-Web/pull/6)
(vendored mirror; the deployed bridge keeps the old behaviour until rebuilt).
Verified with the rebuilt jar: the corpus compiles 0-error (CIF/CIP correctly
gain one W8 warning each on `oInsure`); the 147-test suite passes on
regenerated code; seven deliberately broken probes now fail with the intended
diagnostics — five of them previously passed validation and failed only at
runtime or on-chain. Bonus corpus finding from L9: the `billOfLading` grants
(write `blNumber`; transfer) are given *by seller* although the asset's
declared owner is the *carrier* — flagged as info; worth an ACPolicy review
(grant by carrier, or co-controllers).

*Removed on expert review:*
(4) cross-namespace uniqueness — unnecessary: name resolution is
namespace-aware, so a variable and a domain type may legitimately share a
name;
(5) "violation-triggered obligations should be surviving" — wrong as a
general rule: if the violation is *unhandled* the contract terminates
unsuccessfully and only a surviving obligation survives (the Incoterms
case), but if a power *handles* the violation the contract stays active and
a main-section obligation is exactly right — whereas a surviving one would
never activate;
(7) unset-`Env`-deadline warning — a runtime/input concern, not a static
property (Env values are the runtime's to supply);
(10) "thirdParty role in no Grant" — not a defect: a third party assigned as
performer/controller/owner can already act in that capacity without extra
permissions, and additional rights can be granted or delegated dynamically
at runtime.

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

**Phase 0 — hygiene + static analysis (days; SymboleoAC-IDE/2SC + test network).**
Fix C1/C2 in the code generator (retiring `patchCodegen`); add the C4
generated-JS self-check; C3 dept handling; T3 network fixes; and the **C7
validator rule set** — the error tier (Event performer/controller, reserved
words, unique rule names, cross-namespace uniqueness) plus the warning tier
(violation-triggered-must-survive, missing AC role attributes, unset Env
deadlines, arithmetic-in-consequent). All are `@Check(FAST)` methods in one
file; warnings cannot break existing specs, and the error-tier rules only
reject specs that were already broken downstream. The toolchain for all of
this is local and buildable (the templates live in `Symboleo2SC.xtend` /
`SymboleoValidator.java`, and the fat jar builds from this tree).
*Corpus effect:* none on the matrix; removes two workaround layers, makes the
compile gate trustworthy, and moves four empirically-discovered deployment
failures (untriggerable events, shadowed members, opaque on-chain
"Unauthorized", stillborn reparations) to compile time.

> **Phase 0 status (2026-07-07): C7 implemented (expert-reviewed, PRs
> SymboleoAC-IDE#1 / SymboleoAC-Web#6); C1/C2 fixed and C4 implemented on
> the stacked `claude/phase0-codegen-fixes` branches; W8 retired with C2;
> `patchCodegen` retired in this repo.** Verification sequence worth
> reporting: C4 was built *before* the C2 fix and correctly failed the gate
> on CIF's then-unparseable contract class; after the C2 fix the corpus
> generates 0-error/0-warning and the full suite passes on unpatched
> generator output. Remaining Phase-0 items: C3 dept handling in the
> compiler (the generator side already emits `dept`; the validator error
> E6 covers specs), T3 network fixes (documented in deploy/README.md,
> upstream PR still to file), and the bridge redeploy so CI and the Web
> IDE enforce all of it.

**Phase 1 — runtime semantics (weeks; js-core + codegen).**
R4/O9: violation defers whole-contract termination when a remedial power or
violation-triggered norm exists (or a per-contract policy flag); O10/R-side:
honour antecedents at creation (Create until activated); R1 interval-based
`HappensWithin`. Retire the C7 warning (5) when the violation policy lands.
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

**Phase 3 — ontology↔stack alignment (months; ontology + grammar + runtime).**
The AC ontology is *richer than its implementation and its users*: close that
gap in both directions. Downward: give the ontology's `transfer` and `Revoke`
runtime semantics and Fabric transactions (today only `Grant read/write` are
exercised anywhere), and probe/test `Grant all`; conceptualize the
identity→role authentication mapping that `authenticate` implements (O4a —
`dept` stops being folklore); fix the internal quality items (O4c: undeclared
`Condition`, association typos). Sideways: modularize the core-vs-AC ontology
pair (O4d, Umple mixins) and produce an EMF/diagram model of the AC extension
so the published class diagrams match the deployed language. Upward: O7
`Reparation`; O5 third-party beneficiary via `rightHolder`; O6 surface syntax
for sub-contract references; L5 modules.
*Corpus effect:* B/L endorsement becomes an *executable* transfer (upgrading
the A6 document-of-title story from a recorded grant to enforced semantics);
the insurer direct-claim (A5) and the cost-heads-conditioned-on-the-
carriage-contract (A9/B9) become expressible; the generator's inlined "shared
ontology" becomes a real module; spec LOC drops substantially.

**Phase 4 — research extensions (the JURIX agenda).**
O1 risk, O2 cost algebra, L3 defeasibility, L6 vague standards.
*Corpus effect:* the remaining ◐ rows (A3/B3, A9/B9, the defeaters, the
qualifiers) — the honest frontier.

**Benchmark protocol per phase:** regenerate the 11 specs → 0/0 compile →
147 tests green → power-instance census (currently 48/48) → coverage matrix
re-score (the diff is the phase's measured outcome) → FOB Fabric redeploy for
phases touching codegen/runtime.
