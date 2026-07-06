// Full power-instance coverage: for every rule, every power declared in its
// spec is driven to creation on a breach (or suspend/resume) path — 38 power
// instances across the 11 rules. This substantiates the paper's coverage
// claim behaviourally instead of by extrapolation from power *types*.
//
// The recipes mirror the norm semantics:
//   pTerminateByBuyer            violate oDeliver (F-terms nominate first)
//   pTerminateBySeller           happy trace minus take-over, violate oTakeDelivery
//   pTerminateNoCarriage         violate oContractCarriage
//   pTerminateNoInsurance        violate oInsure
//   pTerminateNoImportClearance  violate oImportClearance (DDP)
//   pSuspendDelivery             violate the nomination obligation
//   pResumeDelivery              nominate -> (late) violate nomination ->
//                                seller suspends oDeliver (harness stands in
//                                for exercising pSuspendDelivery) -> the
//                                nomination is re-evaluated within the
//                                suspension -> resume power created.

import test from 'node:test';
import assert from 'node:assert/strict';
import { ensureGenerated } from './generate.mjs';
import { loadRule, makeContract, fire, violate, suspend, reemit } from './harness.mjs';
import { RULES, effNow } from './scenarios.mjs';

const genDir = await ensureGenerated(RULES.map((r) => r.code));

const F = new Set(['FOB', 'FAS', 'FCA']);
const CARRIAGE = new Set(['CPT', 'CFR', 'CIP', 'CIF', 'DAP', 'DPU', 'DDP']);
const INSURED = new Set(['CIF', 'CIP']);

function expectedPowers(code) {
  const p = ['pTerminateByBuyer', 'pTerminateBySeller'];
  if (F.has(code)) p.push('pSuspendDelivery', 'pResumeDelivery');
  if (CARRIAGE.has(code)) p.push('pTerminateNoCarriage');
  if (INSURED.has(code)) p.push('pTerminateNoInsurance');
  if (code === 'DDP') p.push('pTerminateNoImportClearance');
  return p;
}

// The nomination event of the F-term (first event of its happy trace).
const nominationEvent = (R) => R.happy[0];

function recipe(R, power) {
  switch (power) {
    case 'pTerminateByBuyer':
      return { pre: R.nominates ? [nominationEvent(R)] : [], violate: 'oDeliver' };
    case 'pTerminateBySeller':
      return { pre: R.happy.slice(0, -2), violate: 'oTakeDelivery' };
    case 'pTerminateNoCarriage':
      return { pre: [], violate: 'oContractCarriage' };
    case 'pTerminateNoInsurance':
      return { pre: [], violate: 'oInsure' };
    case 'pTerminateNoImportClearance':
      return { pre: [], violate: 'oImportClearance' };
    case 'pSuspendDelivery':
      return { pre: [], violate: R.nominates };
    default:
      return null; // pResumeDelivery: special-cased below
  }
}

for (const R of RULES) {
  for (const power of expectedPowers(R.code)) {
    if (power === 'pResumeDelivery') {
      // The runtime unsuccessfully terminates the whole contract the moment an
      // obligation is violated, so the suspend->resume cycle is driven without
      // a violation: the seller suspends delivery (harness stands in for the
      // power exercise, a Fabric transaction), the nomination is re-evaluated
      // within the suspension, the resume power appears, the buyer exercises
      // it, and the contract still completes successfully.
      test(`${R.code}: suspend/resume cycle -> pResumeDelivery created, then SuccessfulTermination`, () => {
        const rule = loadRule(genDir, R.code);
        const c = makeContract(rule, R.ctor(effNow()));
        const nom = nominationEvent(R);
        fire(rule, c, nom.event, nom.attrs);            // nomination arrives
        assert.ok(c.obligations.oDeliver != null, `${R.code}: oDeliver not created on nomination`);
        suspend(rule, c, 'oDeliver');                   // seller suspends delivery
        assert.ok(c.obligations.oDeliver.isSuspended(), `${R.code}: oDeliver not suspended`);
        reemit(rule, c, nom.event);                     // nomination re-evaluated within suspension
        assert.ok(c.powers.pResumeDelivery != null,
          `${R.code}: expected pResumeDelivery; have [${Object.keys(c.powers)}]`);
        // The buyer exercises the resume power; the contract then completes.
        c.obligations.oDeliver.resumed();
        assert.ok(!c.obligations.oDeliver.isSuspended(), `${R.code}: oDeliver still suspended`);
        for (const { event, attrs } of R.happy.slice(1)) fire(rule, c, event, attrs);
        assert.ok(c.isSuccessfulTermination(), `${R.code} contract = ${c.state}`);
      });
      continue;
    }
    const r = recipe(R, power);
    test(`${R.code}: power coverage - ${power} created (violate ${r.violate})`, () => {
      const rule = loadRule(genDir, R.code);
      const c = makeContract(rule, R.ctor(effNow()));
      for (const { event, attrs } of r.pre) fire(rule, c, event, attrs);
      assert.ok(c.obligations[r.violate] != null, `${R.code}: no obligation ${r.violate}`);
      violate(rule, c, r.violate);
      assert.ok(c.powers[power] != null,
        `${R.code}: expected ${power}; have [${Object.keys(c.powers)}]`);
    });
  }
}
