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
const NOTICE = 10; const CARRIAGE = 10; const IMPORT = 15; const DELIV = 20; const PAY = 30;

const ev = (event, attrs) => ({ event, attrs });
// A8: checking/packaging/marking precedes delivery in every rule.
const pack = ev('packagedAndMarked');

// Shared tails of the happy trace once the goods are delivered.
const withBoLDocs = [ev('billOfLadingIssued'), ev('documentsProvided'), ev('deliveryNoticeGiven'), ev('goodsTakenOver'), ev('paid')];
const proofDocs = [ev('documentsProvided'), ev('deliveryNoticeGiven'), ev('goodsTakenOver'), ev('paid')];

export const RULES = [
  // --- F-terms: buyer nominates; breach = seller misses delivery ---
  {
    code: 'FOB', nominates: 'oNominateVessel',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, eff, NOTICE, DELIV, PAY],
    happy: [ev('vesselNominated', { loadingPort: ORIGIN }), pack, ev('exportCleared'),
      ev('loadedOnBoard', { port: ORIGIN }), ...withBoLDocs],
    breach: { pre: [ev('vesselNominated', { loadingPort: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'FAS', nominates: 'oNominateVessel',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, eff, NOTICE, DELIV, PAY],
    happy: [ev('vesselNominated', { loadingPort: ORIGIN }), pack, ev('exportCleared'),
      ev('deliveredAlongside', { port: ORIGIN }), ...proofDocs],
    breach: { pre: [ev('vesselNominated', { loadingPort: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'FCA', nominates: 'oNominateCarrier',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, eff, NOTICE, DELIV, PAY],
    happy: [ev('carrierNominated', { namedPlace: ORIGIN }), pack, ev('exportCleared'),
      ev('handedToCarrier', { place: ORIGIN }), ...proofDocs],
    breach: { pre: [ev('carrierNominated', { namedPlace: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  // --- C-terms: seller carriage; oDeliver is unconditional (exists at ctor) ---
  {
    code: 'CFR',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, DEST, eff, NOTICE, CARRIAGE, DELIV, PAY],
    happy: [pack, ev('exportCleared'), ev('carriageContracted'), ev('loadedOnBoard'), ...withBoLDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'CIF',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, DEST, eff, NOTICE, CARRIAGE, DELIV, PAY, 'ICC(C) 110%'],
    happy: [pack, ev('exportCleared'), ev('carriageContracted'),
      ev('insuranceObtained', { insuredAmount: 5500, insuredCurrency: 'USD' }), ev('insuranceDocProvided'),
      ev('loadedOnBoard'), ...withBoLDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted'), ev('insuranceObtained')], violate: 'oInsure', power: 'pTerminateNoInsurance' },
  },
  {
    code: 'CPT',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, DEST, eff, NOTICE, CARRIAGE, DELIV, PAY],
    happy: [pack, ev('exportCleared'), ev('carriageContracted'), ev('handedToFirstCarrier'), ...proofDocs],
    breach: { pre: [ev('exportCleared')], violate: 'oContractCarriage', power: 'pTerminateNoCarriage' },
  },
  {
    code: 'CIP',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, DEST, eff, NOTICE, CARRIAGE, DELIV, PAY, 'ICC(A) 110%'],
    happy: [pack, ev('exportCleared'), ev('carriageContracted'),
      ev('insuranceObtained', { insuredAmount: 5500, insuredCurrency: 'USD' }), ev('insuranceDocProvided'),
      ev('handedToFirstCarrier'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oInsure', power: 'pTerminateNoInsurance' },
  },
  // --- D-terms: seller carriage + delivery at destination ---
  {
    code: 'DAP',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, NOTICE, CARRIAGE, IMPORT, DELIV, PAY],
    happy: [pack, ev('exportCleared'), ev('carriageContracted'), ev('importClearedByBuyer'), ev('madeAvailable'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'DPU',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, NOTICE, CARRIAGE, IMPORT, DELIV, PAY],
    happy: [pack, ev('exportCleared'), ev('carriageContracted'), ev('importClearedByBuyer'), ev('unloadedAtDestination'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'DDP',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, NOTICE, CARRIAGE, DELIV, PAY],
    happy: [pack, ev('exportCleared'), ev('carriageContracted'), ev('importCleared'), ev('madeAvailable'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oImportClearance', power: 'pTerminateNoImportClearance' },
  },
  // --- E-term: minimum seller obligation ---
  {
    code: 'EXW',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, eff, NOTICE, DELIV, PAY],
    happy: [pack, ev('goodsMadeAvailable'), ev('deliveryNoticeGiven'), ev('goodsTakenOver'), ev('paid')],
    breach: { pre: [], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
];

export function effNow() {
  const d = new Date();
  d.setSeconds(0, 0);
  return d.toISOString();
}
