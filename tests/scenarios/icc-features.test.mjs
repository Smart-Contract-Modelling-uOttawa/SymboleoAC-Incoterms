// Scenario tests for the ICC-audit features (see coverage/icc-gap-analysis.md):
//
//  string sale    — A2's alternative performance: the physical delivery event
//                   is replaced by ProcuredSoDelivered; the contract must still
//                   reach SuccessfulTermination (all 10 non-EXW rules).
//  failure costs  — the B3/B9(d) premature risk/cost transfer: a buyer-side
//                   failure (nomination violated / nominee fails / import
//                   clearance violated / EXW take-delivery violated) creates
//                   oFailureCosts, guarded by the goods-identified proviso,
//                   fulfilled by AdditionalCostsPaid.
//  assistance     — the request/risk/cost pattern: request -> assist obligation
//                   -> reimbursement obligation, per direction.
//  FCA B/L        — the optional on-board bill-of-lading mechanism (2020):
//                   agreement -> buyer instructs carrier -> carrier issues ->
//                   seller forwards.

import test from 'node:test';
import assert from 'node:assert/strict';
import { ensureGenerated } from './generate.mjs';
import { loadRule, makeContract, fire, violate } from './harness.mjs';
import { RULES, effNow } from './scenarios.mjs';

const genDir = await ensureGenerated(RULES.map((r) => r.code));
const byCode = Object.fromEntries(RULES.map((r) => [r.code, r]));

// The physical delivery event each rule's happy trace fires (replaced by the
// procurement event on the string-sale path).
const DELIVERY_EVENT = {
  FOB: 'loadedOnBoard', FAS: 'deliveredAlongside', FCA: 'handedToCarrier',
  CPT: 'handedToFirstCarrier', CIP: 'handedToFirstCarrier',
  CFR: 'loadedOnBoard', CIF: 'loadedOnBoard',
  DAP: 'madeAvailable', DPU: 'unloadedAtDestination', DDP: 'madeAvailable',
};

// --- string sales: procure goods so delivered, contract still terminates ---
for (const R of RULES.filter((r) => r.code !== 'EXW')) {
  test(`${R.code}: string sale (procuredSoDelivered) -> SuccessfulTermination`, () => {
    const rule = loadRule(genDir, R.code);
    const c = makeContract(rule, R.ctor(effNow()));
    for (const { event, attrs } of R.happy) {
      if (event === DELIVERY_EVENT[R.code]) fire(rule, c, 'procuredSoDelivered');
      else fire(rule, c, event, attrs);
    }
    for (const [k, o] of Object.entries(c.obligations)) {
      assert.ok(o.isFulfilled(), `${R.code}.obligations.${k} = ${o.state}, expected Fulfillment`);
    }
    for (const [k, o] of Object.entries(c.survivingObligations)) {
      assert.ok(o.isFulfilled(), `${R.code}.survivingObligations.${k} = ${o.state}`);
    }
    assert.ok(c.isSuccessfulTermination(), `${R.code} contract = ${c.state}`);
  });
}

// --- B3/B9(d) failure costs -------------------------------------------------
// {code, pre-events, the failing step (violate obligation or fire third-party
// failure event), extra powers expected alongside oFailureCosts}
const FAILURES = [
  { code: 'FOB', pre: [], violate: 'oNominateVessel' },
  { code: 'FAS', pre: [], violate: 'oNominateVessel' },
  { code: 'FCA', pre: [], violate: 'oNominateCarrier' },
  { code: 'FOB', pre: [], fireEvent: 'vesselFailedToLoad', alsoPower: 'pSuspendDelivery' },
  { code: 'FAS', pre: [], fireEvent: 'vesselFailedToLoad', alsoPower: 'pSuspendDelivery' },
  { code: 'FCA', pre: [], fireEvent: 'carrierFailedToTakeCharge', alsoPower: 'pSuspendDelivery' },
  { code: 'DAP', pre: [], violate: 'oImportClearanceBuyer' },
  { code: 'DPU', pre: [], violate: 'oImportClearanceBuyer' },
  { code: 'EXW', pre: [{ event: 'goodsMadeAvailable' }], violate: 'oTakeDelivery' },
];

for (const FCASE of FAILURES) {
  const how = FCASE.violate ? `violate ${FCASE.violate}` : `fire ${FCASE.fireEvent}`;
  test(`${FCASE.code}: B3/B9(d) failure (${how}) -> oFailureCosts`, () => {
    const R = byCode[FCASE.code];
    const rule = loadRule(genDir, FCASE.code);
    const c = makeContract(rule, R.ctor(effNow()));
    // The ICC proviso: the goods have been clearly identified as the contract
    // goods. Without it the failure-cost obligation must not take effect.
    fire(rule, c, 'goodsIdentified');
    for (const { event, attrs } of FCASE.pre) fire(rule, c, event, attrs);
    if (FCASE.violate) violate(rule, c, FCASE.violate);
    else fire(rule, c, FCASE.fireEvent, { reason: 'closed for cargo early' });

    // A *surviving* obligation: on the violate paths the runtime unsuccessfully
    // terminates the contract the moment the buyer's obligation is violated,
    // and survivingObligations is precisely the section that outlives that -
    // the same device the specs use for the post-termination payment (risk).
    const o = c.survivingObligations.oFailureCosts;
    assert.ok(o != null, `${FCASE.code}: oFailureCosts not created; have [${Object.keys(c.survivingObligations)}]`);
    if (FCASE.alsoPower) {
      assert.ok(c.powers[FCASE.alsoPower] != null,
        `${FCASE.code}: expected ${FCASE.alsoPower} alongside oFailureCosts`);
    }
    fire(rule, c, 'additionalCostsPaid', { amount: 250 });
    assert.ok(o.isFulfilled(), `${FCASE.code}.oFailureCosts = ${o.state}, expected Fulfillment`);
  });
}

// --- assistance channels ------------------------------------------------------
const NO_TO_BUYER = new Set(['DDP']);   // DDP's seller owes no assistance
const NO_TO_SELLER = new Set(['EXW']);  // EXW's buyer owes none

for (const R of RULES) {
  const toBuyer = !NO_TO_BUYER.has(R.code);
  const toSeller = !NO_TO_SELLER.has(R.code);
  test(`${R.code}: assistance round-trip (request -> assist -> reimburse)`, () => {
    const rule = loadRule(genDir, R.code);
    const c = makeContract(rule, R.ctor(effNow()));
    if (toBuyer) {
      fire(rule, c, 'assistanceToBuyerRequested', { topic: 'A7(b) clearance documents' });
      assert.ok(c.obligations.oAssistBuyer != null, `${R.code}: oAssistBuyer not created`);
      fire(rule, c, 'assistanceToBuyerProvided', { topic: 'A7(b) clearance documents' });
      assert.ok(c.obligations.oAssistBuyer.isFulfilled(), `${R.code}: oAssistBuyer = ${c.obligations.oAssistBuyer.state}`);
      assert.ok(c.obligations.oReimburseSellerAssist != null, `${R.code}: oReimburseSellerAssist not created`);
      fire(rule, c, 'assistanceToBuyerReimbursed', { amount: 100 });
      assert.ok(c.obligations.oReimburseSellerAssist.isFulfilled(),
        `${R.code}: oReimburseSellerAssist = ${c.obligations.oReimburseSellerAssist.state}`);
    } else {
      assert.equal(c.assistanceToBuyerRequested, undefined, `${R.code}: unexpected to-buyer channel`);
    }
    if (toSeller) {
      fire(rule, c, 'assistanceToSellerRequested', { topic: 'B7(a) export clearance documents' });
      assert.ok(c.obligations.oAssistSeller != null, `${R.code}: oAssistSeller not created`);
      fire(rule, c, 'assistanceToSellerProvided', { topic: 'B7(a) export clearance documents' });
      assert.ok(c.obligations.oAssistSeller.isFulfilled(), `${R.code}: oAssistSeller = ${c.obligations.oAssistSeller.state}`);
      assert.ok(c.obligations.oReimburseBuyerAssist != null, `${R.code}: oReimburseBuyerAssist not created`);
      fire(rule, c, 'assistanceToSellerReimbursed', { amount: 100 });
      assert.ok(c.obligations.oReimburseBuyerAssist.isFulfilled(),
        `${R.code}: oReimburseBuyerAssist = ${c.obligations.oReimburseBuyerAssist.state}`);
    } else {
      assert.equal(c.assistanceToSellerRequested, undefined, `${R.code}: unexpected to-seller channel`);
    }
  });
}

// --- FCA on-board B/L mechanism ----------------------------------------------
test('FCA: on-board B/L mechanism (agree -> instruct -> issue -> forward)', () => {
  const R = byCode.FCA;
  const rule = loadRule(genDir, 'FCA');
  const c = makeContract(rule, R.ctor(effNow()));
  // Dormant until agreed.
  assert.equal(c.obligations.oInstructCarrierBL, undefined, 'mechanism must be dormant before agreement');
  fire(rule, c, 'onBoardBLAgreed');
  assert.ok(c.obligations.oInstructCarrierBL != null, 'oInstructCarrierBL not created on agreement');
  fire(rule, c, 'blInstructionGiven');
  assert.ok(c.obligations.oInstructCarrierBL.isFulfilled(),
    `oInstructCarrierBL = ${c.obligations.oInstructCarrierBL.state}`);
  // The carrier (a third party not bound by the sale contract) issues.
  fire(rule, c, 'onBoardBLIssued', { blNumber: 'BL-42' });
  assert.ok(c.obligations.oForwardOnBoardBL != null, 'oForwardOnBoardBL not created on issuance');
  fire(rule, c, 'onBoardBLForwarded');
  assert.ok(c.obligations.oForwardOnBoardBL.isFulfilled(),
    `oForwardOnBoardBL = ${c.obligations.oForwardOnBoardBL.state}`);
});
