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
// reimburseDays (L4): "within N days of the assistance being provided". The
// happy/assistance traces fire provided and reimbursed back-to-back (both
// "now"), well inside this window; the L4 witness backdates to breach it.
const REIMB = 30;

const ev = (event, attrs) => ({ event, attrs });
// A8: checking/packaging/marking precedes delivery in every rule.
const pack = ev('packagedAndMarked');
// A1: the commercial invoice (unconditional in every rule).
const invoice = ev('invoiceProvided');

// Shared tails of the happy trace once the goods are delivered.
const withBoLDocs = [ev('billOfLadingIssued', { negotiable: true, originalsCount: 3 }), ev('documentsProvided', { conforming: true }), ev('deliveryNoticeGiven'), ev('goodsTakenOver'), ev('paid')];
const proofDocs = [ev('documentsProvided', { conforming: true }), ev('deliveryNoticeGiven'), ev('goodsTakenOver'), ev('paid')];

export const RULES = [
  // --- F-terms: buyer nominates; breach = seller misses delivery ---
  {
    code: 'FOB', nominates: 'oNominateVessel',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, eff, NOTICE, IMPORT, DELIV, PAY, REIMB],
    happy: [ev('vesselNominated', { loadingPort: ORIGIN }), pack, invoice, ev('securityComplied'),
      ev('exportCleared'), ev('importClearedByBuyer'),
      ev('loadedOnBoard', { port: ORIGIN }), ...withBoLDocs],
    breach: { pre: [ev('vesselNominated', { loadingPort: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'FAS', nominates: 'oNominateVessel',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, eff, NOTICE, IMPORT, DELIV, PAY, REIMB],
    happy: [ev('vesselNominated', { loadingPort: ORIGIN }), pack, invoice, ev('securityComplied'),
      ev('exportCleared'), ev('importClearedByBuyer'),
      ev('deliveredAlongside', { port: ORIGIN }), ...proofDocs],
    breach: { pre: [ev('vesselNominated', { loadingPort: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'FCA', nominates: 'oNominateCarrier',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, eff, NOTICE, IMPORT, DELIV, PAY, REIMB],
    happy: [ev('carrierNominated', { namedPlace: ORIGIN }), pack, invoice, ev('securityComplied'),
      ev('exportCleared'), ev('importClearedByBuyer'),
      ev('handedToCarrier', { place: ORIGIN }), ...proofDocs],
    breach: { pre: [ev('carrierNominated', { namedPlace: ORIGIN }), ev('exportCleared')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  // --- C-terms: seller carriage; oDeliver is unconditional (exists at ctor) ---
  {
    code: 'CFR',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, DEST, eff, NOTICE, CARRIAGE, IMPORT, DELIV, PAY, REIMB],
    happy: [pack, invoice, ev('securityComplied'), ev('exportCleared'), ev('carriageContracted'), ev('importClearedByBuyer'), ev('loadedOnBoard'), ...withBoLDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'CIF',
    ctor: (eff) => [S, B, C, ...GOODS, ORIGIN, DEST, eff, NOTICE, CARRIAGE, IMPORT, DELIV, PAY, REIMB],
    // L2: coverLevel is an ordered-enum ordinal (ICCClause C=0,B=1,A=2); CIF's
    // floor is ICC(C), so obtaining ICC(A)=2 satisfies `coverLevel >= ICC(C)`.
    happy: [pack, invoice, ev('securityComplied'), ev('exportCleared'), ev('carriageContracted'), ev('importClearedByBuyer'),
      ev('insuranceObtained', { insuredAmount: 5500, insuredCurrency: 'USD', coverLevel: 2 }), ev('insuranceDocProvided'),
      ev('loadedOnBoard'), ...withBoLDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted'), ev('insuranceObtained')], violate: 'oInsure', power: 'pTerminateNoInsurance' },
  },
  {
    code: 'CPT',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, DEST, eff, NOTICE, CARRIAGE, IMPORT, DELIV, PAY, REIMB],
    happy: [pack, invoice, ev('securityComplied'), ev('exportCleared'), ev('carriageContracted'), ev('importClearedByBuyer'), ev('handedToFirstCarrier'), ...proofDocs],
    breach: { pre: [ev('exportCleared')], violate: 'oContractCarriage', power: 'pTerminateNoCarriage' },
  },
  {
    code: 'CIP',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, DEST, eff, NOTICE, CARRIAGE, IMPORT, DELIV, PAY, REIMB],
    // L2: CIP's floor is ICC(A) (Incoterms 2020 raised it), so the seller must
    // obtain exactly ICC(A)=2 to satisfy `coverLevel >= ICC(A)`.
    happy: [pack, invoice, ev('securityComplied'), ev('exportCleared'), ev('carriageContracted'), ev('importClearedByBuyer'),
      ev('insuranceObtained', { insuredAmount: 5500, insuredCurrency: 'USD', coverLevel: 2 }), ev('insuranceDocProvided'),
      ev('handedToFirstCarrier'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oInsure', power: 'pTerminateNoInsurance' },
  },
  // --- D-terms: seller carriage + delivery at destination ---
  {
    code: 'DAP',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, NOTICE, CARRIAGE, IMPORT, DELIV, PAY, REIMB],
    happy: [pack, invoice, ev('securityComplied'), ev('exportCleared'), ev('carriageContracted'), ev('importClearedByBuyer'), ev('madeAvailable'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'DPU',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, NOTICE, CARRIAGE, IMPORT, DELIV, PAY, REIMB],
    happy: [pack, invoice, ev('securityComplied'), ev('exportCleared'), ev('carriageContracted'), ev('importClearedByBuyer'), ev('arrivedAtDestination'), ev('unloadedAtDestination'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
  {
    code: 'DDP',
    ctor: (eff) => [S, B, ...GOODS, DEST, eff, NOTICE, CARRIAGE, DELIV, PAY, REIMB],
    happy: [pack, invoice, ev('securityComplied'), ev('exportCleared'), ev('carriageContracted'), ev('importCleared'), ev('madeAvailable'), ...proofDocs],
    breach: { pre: [ev('exportCleared'), ev('carriageContracted')], violate: 'oImportClearance', power: 'pTerminateNoImportClearance' },
  },
  // --- E-term: minimum seller obligation ---
  {
    code: 'EXW',
    ctor: (eff) => [S, B, ...GOODS, ORIGIN, eff, NOTICE, IMPORT, DELIV, PAY, REIMB],
    happy: [pack, invoice, ev('clearedByBuyer'), ev('goodsMadeAvailable'), ev('deliveryNoticeGiven'), ev('goodsTakenOver'), ev('paid')],
    breach: { pre: [], violate: 'oDeliver', power: 'pTerminateByBuyer' },
  },
];

export function effNow() {
  const d = new Date();
  d.setSeconds(0, 0);
  return d.toISOString();
}
