// Scenario execution over the generated JS for all 11 Incoterms rules.
//
//  happy path  — fire every obligation's events in order; assert all
//                obligations (incl. the surviving oPay) reach Fulfillment and
//                the contract reaches SuccessfulTermination.
//  breach path — violate a seller obligation; assert the buyer's corresponding
//                terminate power is created (the remedial lifecycle fires).
//
// Run:  npm run gen && npm test        (CODEGEN_JAR or BACKEND_URL set)

import test from 'node:test';
import assert from 'node:assert/strict';
import { ensureGenerated } from './generate.mjs';
import { loadRule, makeContract, fire, violate } from './harness.mjs';
import { RULES, effNow } from './scenarios.mjs';

const genDir = await ensureGenerated(RULES.map((r) => r.code));

for (const R of RULES) {
  test(`${R.code}: happy path -> SuccessfulTermination`, () => {
    const rule = loadRule(genDir, R.code);
    const c = makeContract(rule, R.ctor(effNow()));
    for (const { event, attrs } of R.happy) fire(rule, c, event, attrs);

    for (const [k, o] of Object.entries(c.obligations)) {
      assert.ok(o.isFulfilled(), `${R.code}.obligations.${k} = ${o.state}, expected Fulfillment`);
    }
    for (const [k, o] of Object.entries(c.survivingObligations)) {
      assert.ok(o.isFulfilled(), `${R.code}.survivingObligations.${k} = ${o.state}, expected Fulfillment`);
    }
    assert.ok(c.isSuccessfulTermination(), `${R.code} contract = ${c.state}, expected SuccessfulTermination`);
  });

  test(`${R.code}: breach (violate ${R.breach.violate}) -> ${R.breach.power}`, () => {
    const rule = loadRule(genDir, R.code);
    const c = makeContract(rule, R.ctor(effNow()));
    for (const { event, attrs } of R.breach.pre) fire(rule, c, event, attrs);

    const obl = c.obligations[R.breach.violate];
    assert.ok(obl != null, `${R.code}: obligation ${R.breach.violate} does not exist to violate`);
    violate(rule, c, R.breach.violate);

    assert.ok(obl.isViolated(), `${R.code}.${R.breach.violate} = ${obl.state}, expected Violation`);
    assert.ok(c.powers[R.breach.power] != null,
      `${R.code}: expected power ${R.breach.power} to be created on breach; have [${Object.keys(c.powers)}]`);
  });
}
