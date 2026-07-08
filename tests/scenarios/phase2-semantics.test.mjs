// Phase-2 witness (catalogue item L2, ordered enumerations). CIP's insurance
// floor is ICC(A); CIF's is ICC(C). The generated oInsure now checks
// `insuranceObtained.coverLevel >= ICCClause(min)` as an ORDINAL comparison
// (the enum generates as { C:0, B:1, A:2 }), so a cover below the minimum
// leaves oInsure unfulfilled. This pins the "at least ICC(x)" semantics the
// language previously could not express (the clause set was a bare string).

import test from 'node:test';
import assert from 'node:assert/strict';
import { ensureGenerated } from './generate.mjs';
import { loadRule, makeContract, fire } from './harness.mjs';
import { RULES, effNow } from './scenarios.mjs';

const genDir = await ensureGenerated(['CIP', 'CIF']);
const CIP = RULES.find((r) => r.code === 'CIP');
const CIF = RULES.find((r) => r.code === 'CIF');

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
