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

test('structural: every spec has the universal norms (package, deliver, take, pay)', () => {
  for (const c of ALL) {
    assert.ok(has(c, /^\s*oPackage:/m), `${c}: missing oPackage (A8)`);
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
    // Wave 2: the 110%-of-price / contract-currency constraints, the
    // policy/certificate obligation, and the War/Strikes conditional.
    assert.equal(has(c, /oInsure:[\s\S]*?insuredAmount >= 1\.1 \* price/), INSURED.has(c), `${c}: 110% constraint`);
    assert.equal(has(c, /^\s*oProvideInsuranceDoc:/m), INSURED.has(c), `${c}: oProvideInsuranceDoc`);
    assert.equal(has(c, /^\s*oAdditionalCover:/m), INSURED.has(c), `${c}: oAdditionalCover`);
    assert.equal(has(c, /^\s*oPayAdditionalCover:/m), INSURED.has(c), `${c}: oPayAdditionalCover`);
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

test('differential: string-sale alternative (procuredSoDelivered) iff not EXW', () => {
  for (const c of ALL) {
    assert.equal(has(c, /ProcuredSoDelivered isAn Event/), c !== 'EXW', `${c}: ProcuredSoDelivered event`);
    assert.equal(has(c, /oDeliver:[\s\S]*?or WhappensBefore\(procuredSoDelivered/), c !== 'EXW',
      `${c}: oDeliver string-sale disjunct`);
  }
});

test('differential: B3/B9(d) failure provisos match the yaml b3_triggers', () => {
  // Since Wave 2 every rule has at least one modelled B3/B9(d) limb.
  for (const c of ALL) {
    assert.ok(has(c, /^\s*oFailureCosts:/m), `${c}: oFailureCosts presence`);
    assert.ok(has(c, /oFailureCosts:[\s\S]*?Happens\(goodsIdentified\)/),
      `${c}: oFailureCosts must be guarded by the goods-identified proviso`);
    // Third-party failure events: vessel for FAS/FOB, carrier for FCA.
    assert.equal(has(c, /VesselFailedToLoad isAn Event/), c === 'FAS' || c === 'FOB', `${c}: VesselFailedToLoad`);
    assert.equal(has(c, /CarrierFailedToTakeCharge isAn Event/), c === 'FCA', `${c}: CarrierFailedToTakeCharge`);
  }
});

test('differential: A10 notice in every rule; conditional B10 schedule notice iff non-F', () => {
  for (const c of ALL) {
    assert.ok(has(c, /^\s*oNotifyDelivery:/m), `${c}: missing oNotifyDelivery (A10)`);
    assert.equal(has(c, /^\s*oNotifySchedule:/m), !F_TERMS.has(c), `${c}: oNotifySchedule presence`);
    // The F-terms' A10 is the dual delivered-or-failed notice.
    if (F_TERMS.has(c)) {
      assert.ok(has(c, /oNotifyDelivery: \([\s\S]*?or Happens\((vesselFailedToLoad|carrierFailedToTakeCharge)\)\)/),
        `${c}: oNotifyDelivery must carry the dual failure limb`);
    }
  }
});

test('differential: buyer-side clearance follows the ICC allocation', () => {
  for (const c of ALL) {
    // Every rule whose import clearance the ICC table assigns to the buyer
    // (all but DDP and EXW) has the first-class buyer obligation; EXW's buyer
    // instead clears everything (export/transit/import).
    assert.equal(has(c, /^\s*oImportClearanceBuyer:/m), c !== 'DDP' && c !== 'EXW',
      `${c}: oImportClearanceBuyer presence`);
    assert.equal(has(c, /^\s*oClearanceBuyer:/m), c === 'EXW', `${c}: oClearanceBuyer presence`);
  }
});

test('differential: A4 security compliance in every rule except EXW', () => {
  for (const c of ALL) {
    assert.equal(has(c, /^\s*oSecurityCompliance:/m), c !== 'EXW', `${c}: oSecurityCompliance presence`);
    // B10 notified content includes transport-security requirements.
    if (c !== 'EXW') {
      assert.ok(has(c, /Env securityRequirements: String/), `${c}: securityRequirements notice content`);
    }
  }
});

test('differential: assistance channels (to-buyer iff not DDP, to-seller iff not EXW)', () => {
  for (const c of ALL) {
    assert.equal(has(c, /^\s*oAssistBuyer:/m), c !== 'DDP', `${c}: oAssistBuyer presence`);
    assert.equal(has(c, /^\s*oReimburseSellerAssist:/m), c !== 'DDP', `${c}: oReimburseSellerAssist presence`);
    assert.equal(has(c, /^\s*oAssistSeller:/m), c !== 'EXW', `${c}: oAssistSeller presence`);
    assert.equal(has(c, /^\s*oReimburseBuyerAssist:/m), c !== 'EXW', `${c}: oReimburseBuyerAssist presence`);
  }
});

test('differential: the on-board B/L mechanism is FCA-only (Incoterms 2020 novelty)', () => {
  for (const c of ALL) {
    assert.equal(has(c, /^\s*oInstructCarrierBL:/m), c === 'FCA', `${c}: oInstructCarrierBL presence`);
    assert.equal(has(c, /^\s*oForwardOnBoardBL:/m), c === 'FCA', `${c}: oForwardOnBoardBL presence`);
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
