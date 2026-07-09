// Phase-2 witnesses (catalogue items L2 ordered enumerations, L4 event-relative
// deadlines).
//
// L2: CIP's insurance floor is ICC(A); CIF's is ICC(C). The generated oInsure
// now checks `insuranceObtained.coverLevel >= ICCClause(min)` as an ORDINAL
// comparison (the enum generates as { C:0, B:1, A:2 }), so a cover below the
// minimum leaves oInsure unfulfilled. This pins the "at least ICC(x)" semantics
// the language previously could not express (the clause set was a bare string).
//
// L4: the assistance-reimbursement obligations now carry a deadline relative to
// when the assistance was *provided* -- WhappensBefore(reimbursed,
// Date.add(provided, reimburseDays, days)), compiling to
// Utils.addTime(contract.<provided>._timestamp, ...). A reimbursement after the
// window leaves the obligation unfulfilled; before it, fulfilled. This deadline
// could not be written before L4 (Date.add's base had to be a contract-param
// date, not an event occurrence). The timely case is also exercised across all
// assistance-bearing rules in icc-features.test.mjs.

import test from 'node:test';
import assert from 'node:assert/strict';
import { ensureGenerated } from './generate.mjs';
import { loadRule, makeContract, fire } from './harness.mjs';
import { RULES, effNow } from './scenarios.mjs';

const genDir = await ensureGenerated(['CIP', 'CIF', 'FOB']);
const CIP = RULES.find((r) => r.code === 'CIP');
const CIF = RULES.find((r) => r.code === 'CIF');
const FOB = RULES.find((r) => r.code === 'FOB');

// Drive a rule's full happy trace but override the obtained coverLevel, and
// report oInsure's final state. oInsure's other conjuncts (delivery ordering,
// insured amount, currency) are all satisfied by the happy trace, so the only
// variable is whether coverLevel clears the rule's ordered-enum floor.
function insureWith(R, coverOrdinal) {
  const rule = loadRule(genDir, R.code);
  const c = makeContract(rule, R.ctor(effNow()));
  for (const { event, attrs } of R.happy) {
    const a = event === 'insuranceObtained'
      ? { ...attrs, coverLevel: coverOrdinal } : attrs;
    fire(rule, c, event, a);
  }
  return c.obligations.oInsure;
}

test('L2: CIP cover ICC(A)=2 satisfies the ICC(A) floor', () => {
  const o = insureWith(CIP, 2);
  assert.ok(o.isFulfilled(), 'ICC(A) meets CIP’s ICC(A) minimum');
});

test('L2: CIP cover ICC(B)=1 is below the ICC(A) floor -> not fulfilled', () => {
  const o = insureWith(CIP, 1);
  assert.ok(!o.isFulfilled(), 'ICC(B) < ICC(A): oInsure must not fulfil');
});

test('L2: CIF cover ICC(C)=0 satisfies the ICC(C) floor (boundary)', () => {
  const o = insureWith(CIF, 0);
  assert.ok(o.isFulfilled(), 'ICC(C) meets CIF’s ICC(C) minimum (>=)');
});

// --- L4: event-relative reimbursement deadline (FOB, to-buyer channel) --------

// Drive the assistance round-trip up to (but not including) the reimbursement,
// leaving oReimburseSellerAssist InEffect with its deadline armed.
function armReimburse(genDir) {
  const rule = loadRule(genDir, 'FOB');
  const c = makeContract(rule, FOB.ctor(effNow()));
  fire(rule, c, 'assistanceToBuyerRequested', { topic: 'A7(b) clearance documents' });
  fire(rule, c, 'assistanceToBuyerProvided', { topic: 'A7(b) clearance documents' });
  const o = c.obligations.oReimburseSellerAssist;
  assert.ok(o != null && o.isInEffect(),
    'oReimburseSellerAssist should be InEffect once assistance is provided');
  return { rule, c, o };
}

test('L4: reimbursement WITHIN reimburseDays fulfils the obligation', () => {
  const { rule, c, o } = armReimburse(genDir);
  // provided and reimbursed both fire "now" -> reimbursed < provided + 30 days.
  fire(rule, c, 'assistanceToBuyerReimbursed', { amount: 100 });
  assert.ok(o.isFulfilled(), `timely reimbursement should fulfil (state=${o.state})`);
});

test('L4: reimbursement AFTER reimburseDays does NOT fulfil (deadline enforced)', () => {
  const { rule, c, o } = armReimburse(genDir);
  // Backdate the assistance-provided occurrence so its deadline
  // Date.add(provided, reimburseDays=30, days) is already in the past; the
  // reimbursement then fires "now", after the window. Under the pre-L4
  // consequent (bare Happens(reimbursed)) this would have fulfilled.
  c.assistanceToBuyerProvided._timestamp = '2020-01-01T00:00:00.000Z';
  fire(rule, c, 'assistanceToBuyerReimbursed', { amount: 100 });
  assert.ok(!o.isFulfilled(),
    `late reimbursement must not fulfil the deadline-bound obligation (state=${o.state})`);
});
