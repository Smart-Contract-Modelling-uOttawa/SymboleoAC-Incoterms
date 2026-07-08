// Phase-1 runtime-semantics witnesses (iteration plan phase 1; catalogue
// items O9/R4, O10, R1). The 147 pre-existing tests pass unchanged on the
// new runtime — these tests pin the *new* behaviours the corpus previously
// could not express, so a regression to the old semantics fails loudly:
//
//   O9/R4  a violation defers whole-contract termination when it is handled
//          (a live remedial power exists), and still terminates when not;
//   O10    an obligation created with an unsatisfied antecedent starts in
//          Create and only reaches InEffect when the antecedent holds;
//   R1     HappensWithin(e, Suspension(x)) is interval-based: an event from
//          before the suspension episode does not count as within it.
//
// Requires the phase-1 symboleoac-js-core (Events.hasLivePower present) and
// the phase-1 codegen (obligation creation routed on the antecedent).

import test from 'node:test';
import assert from 'node:assert/strict';
import { ensureGenerated } from './generate.mjs';
import { loadRule, makeContract, fire, violate, suspend } from './harness.mjs';
import { RULES, effNow } from './scenarios.mjs';

const genDir = await ensureGenerated(['FOB', 'CIF']);
const FOB = RULES.find((r) => r.code === 'FOB');
const CIF = RULES.find((r) => r.code === 'CIF');

test('O9/R4: an UNHANDLED violation still terminates the contract (baseline kept)', () => {
  const rule = loadRule(genDir, 'FOB');
  const c = makeContract(rule, FOB.ctor(effNow()));
  // No power subscribes to oProvideInvoice's violation and no power is live
  // yet, so the violation is unhandled -> unsuccessful termination.
  violate(rule, c, 'oProvideInvoice');
  assert.ok(c.isUnsuccessfulTermination(),
    'unhandled violation should still unsuccessfully terminate the contract');
});

test('O9/R4: a violation is deferred to a live remedial power (new: was a sweep)', () => {
  const rule = loadRule(genDir, 'FOB');
  const c = makeContract(rule, FOB.ctor(effNow()));
  const nom = FOB.happy[0];
  fire(rule, c, nom.event, nom.attrs); // creates oDeliver
  violate(rule, c, 'oDeliver'); // creates pTerminateByBuyer (a live power)
  assert.ok(c.powers.pTerminateByBuyer != null && !c.powers.pTerminateByBuyer.isFinished(),
    'pTerminateByBuyer should be live after the delivery breach');
  // A second, otherwise-unhandled violation: under the old runtime this
  // swept the whole contract (killing the buyer's terminate power); now the
  // decision belongs to the power holder.
  violate(rule, c, 'oProvideInvoice');
  assert.ok(!c.isUnsuccessfulTermination(),
    'the contract must stay alive while a remedial power is pending');
  assert.ok(!c.powers.pTerminateByBuyer.isFinished(),
    'the pending remedial power must survive the second violation');
  assert.ok(c.obligations.oProvideInvoice.isViolated(),
    'the violation itself is still recorded');
});

test('O10: an obligation with an unsatisfied antecedent starts in Create, not InEffect', () => {
  const rule = loadRule(genDir, 'CIF');
  const c = makeContract(rule, CIF.ctor(effNow()));
  // Trigger the conditional obligation WITHOUT its antecedent: the buyer
  // requests additional cover but has not yet given the information.
  fire(rule, c, 'additionalCoverRequested');
  const o = c.obligations.oAdditionalCover;
  assert.ok(o != null, 'oAdditionalCover should be created by its trigger');
  assert.ok(o.isCreated(), 'antecedent unsatisfied -> Create (ontology: triggeredConditional)');
  assert.ok(!o.isInEffect(), 'must NOT be InEffect before the antecedent holds');
  // The antecedent arrives: the existing activate listener moves it along.
  fire(rule, c, 'additionalCoverInfoGiven');
  assert.ok(o.isInEffect(), 'antecedent satisfied -> InEffect (Create --activated-->)');
  // And it can then be fulfilled normally.
  fire(rule, c, 'additionalCoverObtained');
  assert.ok(o.isFulfilled(), 'the activated obligation fulfills on its consequent');
});

test('R1: an event from before the suspension is not HappensWithin it', () => {
  const rule = loadRule(genDir, 'FOB');
  const c = makeContract(rule, FOB.ctor(effNow()));
  const nom = FOB.happy[0];
  fire(rule, c, nom.event, nom.attrs);
  suspend(rule, c, 'oDeliver');
  const { Predicates } = rule.core;
  // Backdate the nomination to before the suspension episode (timestamps
  // have minute granularity, so a same-minute event is inclusive by design;
  // an earlier one must be excluded — the old state-based check accepted it).
  const original = c.vesselNominated._timestamp;
  c.vesselNominated._timestamp = '2020-01-01T00:00:00.000Z';
  assert.equal(
    Predicates.happensWithin(c.vesselNominated, c.obligations.oDeliver, 'Obligation.Suspension'),
    false,
    'a pre-suspension event must not count as within the suspension',
  );
  c.vesselNominated._timestamp = original;
  assert.equal(
    Predicates.happensWithin(c.vesselNominated, c.obligations.oDeliver, 'Obligation.Suspension'),
    true,
    'an event inside the (open) suspension episode counts',
  );
});
