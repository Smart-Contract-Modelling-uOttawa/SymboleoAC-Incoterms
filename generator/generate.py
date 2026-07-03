#!/usr/bin/env python3
"""Table-driven SymboleoAC generator for the Incoterms 2020 rules.

Reads the ICC allocation tables (``incoterms.data.yaml``) and emits one
``specs/<CODE>.symboleo`` per rule from a shared domain ontology + a library of
norm templates. The 11 specs are kept structurally parallel so coverage claims
and differential tests are apples-to-apples.

Bootstrapping status: the emitter reproduces the golden ``specs/FOB.symboleo``
byte-for-byte (content), then compiles clean. The other rules are layered on by
extending the per-family selection in ``rule_config`` and the section emitters.

Usage:
    python generator/generate.py [--only FOB[,FAS,...]] [--out specs] [--check]
    python generator/generate.py --stdout FOB      # print one spec, emit nothing

``--check`` writes to a scratch dir and diffs against the committed specs
instead of overwriting them (used by CI / the regeneration test).

Output is LF-terminated (see .gitattributes: *.symboleo eol=lf) and deterministic.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "generator" / "incoterms.data.yaml"
NL = "\n"

# --- rule configuration ------------------------------------------------------


@dataclass
class RuleConfig:
    """One rule's generation inputs: the YAML row plus derived modelling choices."""

    code: str
    name: str
    family: str  # sea | any_mode
    delivery_point: str
    seller_insurance: bool
    export_clearance: str  # seller | buyer
    import_clearance: str
    cost: list[str]
    insurance_cover: str | None = None
    # derived — see derive():
    buyer_nominates_vessel: bool = field(default=False)

    @property
    def domain_name(self) -> str:
        return f"{self.code.lower()}Domain"


def load_rules() -> dict[str, RuleConfig]:
    doc = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    rules: dict[str, RuleConfig] = {}
    for code, row in doc["rules"].items():
        cfg = RuleConfig(
            code=code,
            name=row["name"],
            family=row["family"],
            delivery_point=row["delivery_point"],
            seller_insurance=bool(row["seller_insurance"]),
            export_clearance=row["export_clearance"],
            import_clearance=row["import_clearance"],
            cost=list(row["cost"]),
            insurance_cover=row.get("insurance_cover"),
        )
        derive(cfg)
        rules[code] = cfg
    return rules


def derive(cfg: RuleConfig) -> None:
    """Fill modelling choices implied by the ICC row.

    FOB/FAS are the sea F-terms: the *buyer* contracts carriage and nominates
    the vessel, then the seller delivers to it. (CFR/CIF put carriage on the
    seller, so no buyer vessel nomination — layered in a later milestone.)
    """
    cfg.buyer_nominates_vessel = cfg.code in ("FOB", "FAS")


# --- section emitters --------------------------------------------------------
# Each returns the section's lines (no trailing blank line); assemble() joins
# them with blank separators, matching the golden layout.


def emit_domain(c: RuleConfig) -> list[str]:
    L = [f"Domain {c.domain_name}"]
    L += [
        "  // FOB - Free on Board (Incoterms 2020), named port of shipment.",
        "  // Seller bears cost and risk up to the moment the goods are on board the",
        "  // vessel nominated by the buyer; risk then passes to the buyer.",
        "  Seller isA Role with name: String, org: String;",
        "  Buyer isA Role with name: String, org: String;",
        "  // The carrier operates the vessel the buyer nominates; it issues the bill of lading.",
        "  Carrier isA Role thirdParty with name: String, org: String;",
        "  Currency isAn Enumeration(CAD, USD, EUR);",
        "  // The goods sold; owner defaults to the seller until delivery.",
        "  Goods isAn Asset with description: String, quantity: Number, owner: Seller;",
        "  // The bill of lading: the transport document evidencing shipment on board.",
        "  BillOfLading isAn Asset with blNumber: String, owner: Carrier;",
        "  // Buyer nominates the vessel and gives notice (name, loading point, deadline).",
        "  VesselNominated isAn Event with Env vesselName: String, Env loadingPort: String, dueDate: Date, performer: Buyer, controller: Buyer;",
        "  // Seller clears the goods for export.",
        "  ExportCleared isAn Event with performer: Seller, controller: Seller;",
        "  // Delivery: seller places the goods on board the nominated vessel (risk passes).",
        "  LoadedOnBoard isAn Event with port: String, Env onBoardDate: Date, delDueDate: Date, performer: Seller, controller: Seller;",
        "  // Carrier issues the bill of lading once the goods are on board.",
        "  BillOfLadingIssued isAn Event with Env blNumber: String, performer: Carrier, controller: Carrier;",
        "  // Seller hands the buyer the usual proof of delivery (the bill of lading).",
        "  DocumentsProvided isAn Event with performer: Seller, controller: Seller;",
        "  // Buyer takes delivery of the goods.",
        "  GoodsTakenOver isAn Event with performer: Buyer, controller: Buyer;",
        "  // Buyer pays the price.",
        "  Paid isAn Event with amount: Number, currency: Currency, from: Buyer, to: Seller, payDueDate: Date, performer: Buyer, controller: Buyer;",
        "endDomain",
    ]
    return L


def emit_contract_header(c: RuleConfig) -> list[str]:
    return [
        f"Contract {c.code} (",
        "  sellerP: Seller, buyerP: Buyer, carrierP: Carrier,",
        "  goodsDesc: String, qty: Number, price: Number, curr: Currency,",
        "  portOfShipment: String, effDate: Date, noticeDays: Number, deliveryDays: Number, paymentDays: Number",
        ")",
    ]


def emit_declarations(c: RuleConfig) -> list[str]:
    return [
        "Declarations",
        "  seller: Seller with name := sellerP.name, org := sellerP.org;",
        "  buyer: Buyer with name := buyerP.name, org := buyerP.org;",
        "  carrier: Carrier with name := carrierP.name, org := carrierP.org;",
        "  goods: Goods with description := goodsDesc, quantity := qty, owner := seller;",
        '  billOfLading: BillOfLading with blNumber := "", owner := carrier;',
        "  vesselNominated: VesselNominated with dueDate := Date.add(effDate, noticeDays, days), performer := buyer, controller := buyer;",
        "  exportCleared: ExportCleared with performer := seller, controller := seller;",
        "  loadedOnBoard: LoadedOnBoard with port := portOfShipment, delDueDate := Date.add(effDate, deliveryDays, days), performer := seller, controller := seller;",
        "  billOfLadingIssued: BillOfLadingIssued with performer := carrier, controller := carrier;",
        "  documentsProvided: DocumentsProvided with performer := seller, controller := seller;",
        "  goodsTakenOver: GoodsTakenOver with performer := buyer, controller := buyer;",
        "  paid: Paid with amount := price, currency := curr, from := buyer, to := seller, payDueDate := Date.add(effDate, paymentDays, days), performer := buyer, controller := buyer;",
    ]


def emit_preconditions(c: RuleConfig) -> list[str]:
    return ["Preconditions", "  goods.quantity > 0;"]


def emit_obligations(c: RuleConfig) -> list[str]:
    return [
        "Obligations",
        "  // A7: the seller clears the goods for export before they go on board.",
        "  oExportClearance: O(seller, buyer, true, ShappensBefore(exportCleared, loadedOnBoard));",
        "  // A2 delivery: once the buyer has nominated the vessel, the seller must place",
        "  // the goods on board it, at the named loading point, before the deadline.",
        "  oDeliver: Happens(vesselNominated) -> O(seller, buyer, true,",
        "              WhappensBefore(loadedOnBoard, loadedOnBoard.delDueDate)",
        "              and loadedOnBoard.port == vesselNominated.loadingPort);",
        "  // A6: after loading, the carrier issues the bill of lading and the seller",
        "  // provides the buyer with that proof of delivery.",
        "  oProvideDocuments: Happens(loadedOnBoard) -> O(seller, buyer, true,",
        "              Happens(billOfLadingIssued) and Happens(documentsProvided));",
        "  // B7/B10: the buyer nominates the vessel and gives sufficient notice in time.",
        "  oNominateVessel: O(buyer, seller, true, WhappensBefore(vesselNominated, vesselNominated.dueDate));",
        "  // B2: the buyer takes delivery of the goods once they are on board.",
        "  oTakeDelivery: Happens(loadedOnBoard) -> O(buyer, seller, true, Happens(goodsTakenOver));",
    ]


def emit_surviving(c: RuleConfig) -> list[str]:
    return [
        "Surviving Obligations",
        "  // B1: the buyer must pay the price for goods delivered on board and evidenced",
        "  // by the bill of lading; this survives termination of the contract.",
        "  oPay: (Happens(loadedOnBoard) and Happens(documentsProvided)) -> Obligation(buyer, seller, true,",
        "              WhappensBefore(paid, paid.payDueDate) and paid.amount == price);",
    ]


def emit_powers(c: RuleConfig) -> list[str]:
    return [
        "Powers",
        "  // If the buyer fails to nominate the vessel in time, the seller may suspend delivery.",
        "  pSuspendDelivery: Happens(Violated(obligations.oNominateVessel)) ->",
        "              P(seller, buyer, true, Suspended(obligations.oDeliver)) with Controller seller;",
        "  // A late nomination during the suspension resumes the delivery obligation.",
        "  pResumeDelivery: HappensWithin(vesselNominated, Suspension(obligations.oDeliver)) ->",
        "              P(buyer, seller, true, Resumed(obligations.oDeliver));",
        "  // If the seller fails to deliver on board, the buyer may terminate the contract.",
        "  pTerminateByBuyer: Happens(Violated(obligations.oDeliver)) -> P(buyer, seller, true, Terminated(self));",
        "  // If the buyer fails to take delivery, the seller may terminate the contract.",
        "  pTerminateBySeller: Happens(Violated(obligations.oTakeDelivery)) -> P(seller, buyer, true, Terminated(self));",
    ]


def emit_acpolicy(c: RuleConfig) -> list[str]:
    return [
        "ACPolicy with Controller seller",
        "  Rule1: Grant read To buyer On goods.description by seller;",
        "  Rule2: Grant read To buyer On obligations.oDeliver by seller;",
        "  Rule3: Grant read To carrier On loadedOnBoard by seller;",
        "  Rule4: Grant read To seller On billOfLadingIssued by carrier;",
        "  Rule5: Grant write To carrier On billOfLading.blNumber by seller;",
        "  Rule6: Grant write To buyer On powers.pTerminateByBuyer by seller;",
    ]


def emit_constraints(c: RuleConfig) -> list[str]:
    return ["Constraints", "  not(IsEqual(buyer, seller));"]


def assemble(c: RuleConfig) -> str:
    """Join sections in the grammar's required order, blank-line separated."""
    sections = [
        emit_domain(c),
        emit_contract_header(c),
        emit_declarations(c),
        emit_preconditions(c),
        emit_obligations(c),
        emit_surviving(c),
        emit_powers(c),
        emit_acpolicy(c),
        emit_constraints(c),
    ]
    body = (NL + NL).join(NL.join(s) for s in sections)
    return body + NL + NL + "endContract" + NL


# --- CLI ---------------------------------------------------------------------


def write_spec(path: Path, text: str) -> None:
    # Force LF regardless of platform (see .gitattributes).
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="comma-separated rule codes (default: all implemented)")
    ap.add_argument("--out", default=str(REPO / "specs"), help="output dir (default: specs/)")
    ap.add_argument("--stdout", metavar="CODE", help="print one spec to stdout, write nothing")
    ap.add_argument("--check", action="store_true", help="diff against committed specs, don't write")
    args = ap.parse_args(argv)

    rules = load_rules()
    # Milestone 2: only FOB is reproduced; extend this set as rules land.
    implemented = ["FOB"]

    if args.stdout:
        code = args.stdout.upper()
        if code not in rules:
            return _err(f"unknown rule {code}")
        sys.stdout.write(assemble(rules[code]))
        return 0

    codes = [c.upper() for c in args.only.split(",")] if args.only else implemented
    out_dir = Path(args.out)
    rc = 0
    for code in codes:
        if code not in rules:
            rc = _err(f"unknown rule {code}") or rc
            continue
        text = assemble(rules[code])
        target = out_dir / f"{code}.symboleo"
        if args.check:
            existing = target.read_text(encoding="utf-8").replace("\r\n", "\n") if target.exists() else None
            if existing != text:
                print(f"DRIFT  {code}: generated output differs from {target}")
                rc = 1
            else:
                print(f"OK     {code}: matches {target}")
        else:
            write_spec(target, text)
            print(f"wrote  {target}")
    return rc


def _err(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
