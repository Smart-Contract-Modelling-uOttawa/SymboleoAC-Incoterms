// Per-rule scenario data: constructor arguments, the happy-path event trace
// (all obligations fulfilled in order -> SuccessfulTermination), and a breach
// (violate a seller obligation -> the buyer's terminate power is created).
//
// Event attributes only need setting where a predicate compares an Env value
// that the constructor can't fix: the F-term delivery-point match compares the
// delivery event's place against the buyer's nomination (Env), so we stamp the
// nomination (and, harmlessly, the delivery) with the agreed place. Everything
// else (amounts, C/D delivery place, deadlines) is fixed by the constructor.

const S = { name: 'Acme', org: 'AcmeCo' };
const B = { name: 'Buyer', org: 'BuyCo' };
const C = { name: 'Carrier', org: 'CarrCo' };
const GOODS = ['Widgets', 100, 5000, 'USD']; // goodsDesc, qty, price, curr
const ORIGIN = 'OriginPlace';
const DEST = 'DestPlace';
// Deadlines (days from effDate). Events fire "now" (== effDate), before all.
const NOTICE = 10; const CARRIAGE = 10; const DELIV = 20; const PAY = 30;

const ev = (event, attrs) => ({ event, attrs });

// Shared tails of the happy trace once the goods are delivered.
const withBoLDocs = [ev('billOfLadingIssued'), ev('documentsProvided'), ev('goodsTakenOver'), ev('paid')];
const proofDocs = [ev('documentsProvided'), ev('goodsTakenOver'), ev('paid')];

export const RULES = [
  // --- F-terms: buyer nominates; breach = seller misses delivery ---
  {
    code: 'FOB',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, eff, NOTICE, DELIV, PAY],
    happy: [ev('vesselNominated', { loadingPort: ORIGIN }), ev('exportCleared'),
      ev('loadedOnBoard', { port: ORIGIN }), ...withBoLDocs],
    breach: { pre: [ev('vesselNominated', { loadingPort: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'FAS',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, eff, NOTICE, DELIV, PAY],
    happy: [ev('vesselNominated', { loadingPort: ORIGIN }), ev('exportCleared'),
      ev('deliveredAlongside', { port: ORIGIN }), ...proofDocs],
    breach: { pre: [ev('vesselNominated', { loadingPort: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'FCA',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, eff, NOTICE, DELIV, PAY],
    happy: [ev('carrierNominated', { namedPlace: ORIGIN }), ev('exportCleared'),
      ev('handedToCarrier', { place: ORIGIN }), ...proofDocs],
    breach: { pre: [ev('carrierNominated', { namedPlace: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  // --- C-terms: seller carriage; oDeliver is unconditional (exists at ctor) ---
  {
    code: 'CFR',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, DEST, eff, CARRIAGE, DELIV, PAY],
    happy: [ev('exportCleared'), ev('carriageContracted'), ev('loadedOnBoard'), ...withBoLDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'CIF',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, DEST, eff, CARRIAGE, DELIV, PAY, 'ICC(C) 110%'],
    happy: [ev('exportCleared'), ev('carriageContracted'), ev('insuranceObtained'), ev('loadedOnBoard'), ...withBoLDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted'), ev('insuranceObtained')], violate: 'oInsure', power: 'pTerminateNoInsurance' },
  },
  {
    code: 'CPT',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, DEST, eff, CARRIAGE, DELIV, PAY],
    happy: [ev('exportCleared'), ev('carriageContracted'), ev('handedToFirstCarrier'), ...proofDocs],
    breach: { pre: [ev('exportCleared')], violate: 'oContractCarriage', power: 'pTerminateNoCarriage' },
  },
  {
    code: 'CIP',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, DEST, eff, CARRIAGE, DELIV, PAY, 'ICC(A) 110%'],
    happy: [ev('exportCleared'), ev('carriageContracted'), ev('insuranceObtained'), ev('handedToFirstCarrier'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oInsure', power: 'pTerminateNoInsurance' },
  },
  // --- D-terms: seller carriage + delivery at destination ---
  {
    code: 'DAP',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, CARRIAGE, DELIV, PAY],
    happy: [ev('exportCleared'), ev('carriageContracted'), ev('madeAvailable'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'DPU',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, CARRIAGE, DELIV, PAY],
    happy: [ev('exportCleared'), ev('carriageContracted'), ev('unloadedAtDestination'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'DDP',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, CARRIAGE, DELIV, PAY],
    happy: [ev('exportCleared'), ev('carriageContracted'), ev('importCleared'), ev('madeAvailable'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oImportClearance', power: 'pTerminateNoImportClearance' },
  },
  // --- E-term: minimum seller obligation ---
  {
    code: 'EXW',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, eff, DELIV, PAY],
    happy: [ev('goodsMadeAvailable'), ev('goodsTakenOver'), ev('paid')],
    breach: { pre: [], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
];

export function effNow() {
  const d = new Date();
  d.setSeconds(0, 0);
  return d.toISOString();
}
