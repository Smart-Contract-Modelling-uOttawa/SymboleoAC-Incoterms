// Structural + differential checks over the committed specifications (STRATEGY
// sec.3.2/3.4). These are static (they read specs/*.symboleo, no generation) and
// encode the inter-rule invariants implied by the ICC tables, guarding against
// generator drift and dangling cross-references.

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const SPECS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'specs');
const ALL = ['EXW', 'FCA', 'FAS', 'FOB', 'CPT', 'CFR', 'CIP', 'CIF', 'DAP', 'DPU', 'DDP'];
const F_TERMS = new Set(['FOB', 'FAS', 'FCA']);
const C_TERMS = new Set(['CPT', 'CFR', 'CIP', 'CIF']);
const D_TERMS = new Set(['DAP', 'DPU', 'DDP']);
const INSURED = new Set(['CIF', 'CIP']);

const src = Object.fromEntries(ALL.map((c) => [c, readFileSync(path.join(SPECS, `${c}.symboleo`), 'utf8')]));
const has = (code, re) => re.test(src[code]);

test('structural: every spec has the universal norms (deliver, take, pay)', () => {
  for (const c of ALL) {
    assert.ok(has(c, /^\s*oDeliver:/m), `${c}: missing oDeliver`);
    assert.ok(has(c, /^\s*oTakeDelivery:/m), `${c}: missing oTakeDelivery`);
    assert.ok(has(c, /^\s*oPay:/m), `${c}: missing surviving oPay`);
    assert.ok(has(c, /^\s*pTerminateByBuyer:/m), `${c}: missing pTerminateByBuyer`);
    assert.ok(has(c, /^\s*pTerminateBySeller:/m), `${c}: missing pTerminateBySeller`);
  }
});

test('differential: seller insurance obligation iff CIF/CIP', () => {
  for (const c of ALL) {
    assert.equal(has(c, /^\s*oInsure:/m), INSURED.has(c), `${c}: oInsure presence`);
    assert.equal(has(c, /^\s*pTerminateNoInsurance:/m), INSURED.has(c), `${c}: pTerminateNoInsurance`);
  }
});

test('differential: seller carriage obligation iff a C- or D-term', () => {
  for (const c of ALL) {
    const expected = C_TERMS.has(c) || D_TERMS.has(c);
    assert.equal(has(c, /^\s*oContractCarriage:/m), expected, `${c}: oContractCarriage presence`);
  }
});

test('differential: buyer nomination + suspend/resume powers iff an F-term', () => {
  for (const c of ALL) {
    assert.equal(has(c, /^\s*oNominate\w+:/m), F_TERMS.has(c), `${c}: oNominate presence`);
    assert.equal(has(c, /^\s*pSuspendDelivery:/m), F_TERMS.has(c), `${c}: pSuspendDelivery`);
    assert.equal(has(c, /^\s*pResumeDelivery:/m), F_TERMS.has(c), `${c}: pResumeDelivery`);
  }
});

test('differential: seller import clearance iff DDP', () => {
  for (const c of ALL) {
    assert.equal(has(c, /^\s*oImportClearance:/m), c === 'DDP', `${c}: oImportClearance presence`);
  }
});

test('differential: export clearance for every rule except EXW', () => {
  for (const c of ALL) {
    assert.equal(has(c, /^\s*oExportClearance:/m), c !== 'EXW', `${c}: oExportClearance presence`);
  }
});

test('differential: D-terms deliver at destination, others at origin', () => {
  for (const c of D_TERMS) {
    assert.ok(has(c, /oDeliver:[\s\S]*?== placeOfDestination\)/), `${c}: oDeliver should match placeOfDestination`);
  }
  for (const c of [...C_TERMS].filter((x) => !D_TERMS.has(x))) {
    assert.ok(!has(c, /oDeliver:[\s\S]*?== placeOfDestination\)/), `${c}: C-term must not deliver at destination`);
  }
});

test('structural: all obligations.X / powers.X references resolve', () => {
  for (const c of ALL) {
    const s = src[c];
    const oblNames = new Set([...s.matchAll(/^\s*(o[A-Z]\w*):/gm)].map((m) => m[1]));
    const powNames = new Set([...s.matchAll(/^\s*(p[A-Z]\w*):/gm)].map((m) => m[1]));
    for (const m of s.matchAll(/obligations\.(\w+)/g)) {
      assert.ok(oblNames.has(m[1]), `${c}: dangling obligations.${m[1]}`);
    }
    for (const m of s.matchAll(/powers\.(\w+)/g)) {
      assert.ok(powNames.has(m[1]), `${c}: dangling powers.${m[1]}`);
    }
  }
});
