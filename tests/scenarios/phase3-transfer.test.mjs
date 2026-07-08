// Phase-3 witness (catalogue item O4b "downward"): the bill of lading's
// endorsement is now an EXECUTABLE transfer, not just a recorded grant.
// CIF's ACPolicy grants the buyer transfer rights over billOfLading (the A6
// document-of-title device); the seller owns the document (the carrier
// issues it to the shipper -- see the L9 resolution). With the phase-3
// js-core, that grant authorizes a permission-checked ownership
// reassignment, and ownership itself conveys the right to endorse onward.
//
// Requires the phase-3 symboleoac-js-core (ACPolicy.transferResource).

import test from 'node:test';
import assert from 'node:assert/strict';
import { ensureGenerated } from './generate.mjs';
import { loadRule, makeContract } from './harness.mjs';
import { RULES, effNow } from './scenarios.mjs';

const genDir = await ensureGenerated(['CIF']);
const CIF = RULES.find((r) => r.code === 'CIF');

test('O4b: the buyer exercises its transfer grant — the B/L endorsement', () => {
  const rule = loadRule(genDir, 'CIF');
  const c = makeContract(rule, CIF.ctor(effNow()));
  assert.equal(c.billOfLading.owner._name, c.seller._name,
    'the shipper owns the issued document (L9 resolution)');
  // The spec's Grant transfer To buyer On billOfLading (by seller, the
  // policy controller) authorizes the endorsement to the buyer.
  assert.ok(c.accessPolicy.transferResource(c.billOfLading, c.buyer, c.buyer),
    'the buyer holds an explicit transfer grant');
  assert.equal(c.billOfLading.owner._name, c.buyer._name,
    'ownership of the document moved to the buyer');
  // The buyer, now the holder, can endorse onward without any further
  // grant (sale in transit): ownership conveys the transfer right.
  assert.ok(c.accessPolicy.transferResource(c.billOfLading, c.buyer, c.seller),
    'the holder endorses onward');
  assert.equal(c.billOfLading.owner._name, c.seller._name);
});

test('O4b: a role without the grant cannot transfer the B/L', () => {
  const rule = loadRule(genDir, 'CIF');
  const c = makeContract(rule, CIF.ctor(effNow()));
  assert.equal(c.accessPolicy.transferResource(c.billOfLading, c.carrier, c.carrier), false,
    'the carrier holds no transfer right over the issued document');
  assert.equal(c.billOfLading.owner._name, c.seller._name, 'ownership unchanged');
});
