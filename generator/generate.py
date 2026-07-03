#!/usr/bin/env python3
"""Table-driven SymboleoAC generator for the Incoterms 2020 rules.

Reads the ICC allocation tables (``incoterms.data.yaml``) and emits one
``specs/<CODE>.symboleo`` per rule from a shared domain ontology + a library of
norm templates. The 11 specs are kept structurally parallel — they share the
vocabulary and the template *shapes* — while each declares only the
events/assets/norms that its Incoterms rule actually uses (faithful per-rule
modelling). The varying tokens live in a per-rule ``Profile``.

Implemented so far — the sea family:
  * F-terms (buyer contracts carriage + nominates the vessel): FOB, FAS.
  * C-terms (seller contracts carriage to destination; risk still passes on
    board at shipment; CIF adds seller insurance): CFR, CIF.
FOB is reproduced byte-for-byte from the golden spec. The remaining rules extend
``profile_for`` + the section emitters.

Usage:
    python generator/generate.py [--only FOB[,FAS,...]] [--out specs] [--check]
    python generator/generate.py --stdout FOB      # print one spec, emit nothing

``--check`` diffs generated output against the committed specs instead of
overwriting them (used by CI / the regeneration guard).

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

# Which rules the emitters currently reproduce (grows as rules land).
IMPLEMENTED = ["CFR", "CIF", "FAS", "FOB"]


# --- rule configuration ------------------------------------------------------


@dataclass
class Profile:
    """The per-rule tokens the shared templates vary on (faithful modelling)."""

    term_type: str               # "F" (buyer nominates) | "C" (seller carriage)
    domain_comment: list[str]    # the lines under `Domain <x>`
    # Delivery event (where risk passes).
    delivery_event: str          # e.g. "LoadedOnBoard"
    delivery_var: str            # e.g. "loadedOnBoard"
    delivery_date_attr: str      # Env date attr, e.g. "onBoardDate"
    delivery_domain_comment: str
    documents_domain_comment: str
    contract_params_tail: str    # the places/deadlines param line
    # Short phrases woven into the norm comments.
    point_phrase: str            # "on board" | "alongside"
    export_before_phrase: str    # "they go on board" | "they are placed alongside"
    deliver_place_phrase: str    # F-terms: "on board it" | "alongside it"
    provide_docs_line2: str      # 2nd comment line of the BoL document norm
    # Feature switches (approach A: declare only what the rule uses).
    has_carrier: bool
    has_bol: bool                # carrier-issued bill of lading in the doc norm
    has_vessel_nomination: bool  # F-terms
    has_seller_carriage: bool    # C-terms
    has_insurance: bool          # CIF
    insurance_cover: str | None = None


@dataclass
class RuleConfig:
    """One rule's generation inputs: the YAML row plus a derived Profile."""

    code: str
    name: str
    family: str  # sea | any_mode
    delivery_point: str
    seller_insurance: bool
    export_clearance: str  # seller | buyer
    import_clearance: str
    cost: list[str]
    insurance_cover: str | None = None
    profile: Profile = field(init=False)

    @property
    def domain_name(self) -> str:
        return f"{self.code.lower()}Domain"


def load_rules() -> dict[str, RuleConfig]:
    doc = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    rules: dict[str, RuleConfig] = {}
    for code, row in doc["rules"].items():
        rules[code] = RuleConfig(
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
    return rules


# Shared params line for the sea F-terms (buyer nomination notice deadline).
_F_PARAMS = "  portOfShipment: String, effDate: Date, noticeDays: Number, deliveryDays: Number, paymentDays: Number"
# Shared params line for the sea C-terms (destination port + carriage deadline).
_C_PARAMS = "  portOfShipment: String, portOfDestination: String, effDate: Date, carriageDays: Number, deliveryDays: Number, paymentDays: Number"


def profile_for(c: RuleConfig) -> Profile:
    """Build the per-rule Profile. Implemented: the sea family FOB/FAS/CFR/CIF."""
    if c.code == "FOB":
        return Profile(
            term_type="F",
            domain_comment=[
                "  // FOB - Free on Board (Incoterms 2020), named port of shipment.",
                "  // Seller bears cost and risk up to the moment the goods are on board the",
                "  // vessel nominated by the buyer; risk then passes to the buyer.",
            ],
            delivery_event="LoadedOnBoard",
            delivery_var="loadedOnBoard",
            delivery_date_attr="onBoardDate",
            delivery_domain_comment="  // Delivery: seller places the goods on board the nominated vessel (risk passes).",
            documents_domain_comment="  // Seller hands the buyer the usual proof of delivery (the bill of lading).",
            contract_params_tail=_F_PARAMS,
            point_phrase="on board",
            export_before_phrase="they go on board",
            deliver_place_phrase="on board it",
            provide_docs_line2="  // provides the buyer with that proof of delivery.",
            has_carrier=True,
            has_bol=True,
            has_vessel_nomination=True,
            has_seller_carriage=False,
            has_insurance=False,
        )
    if c.code == "FAS":
        return Profile(
            term_type="F",
            domain_comment=[
                "  // FAS - Free Alongside Ship (Incoterms 2020), named port of shipment.",
                "  // Seller bears cost and risk up to the moment the goods are placed alongside",
                "  // the vessel nominated by the buyer; risk then passes to the buyer.",
            ],
            delivery_event="DeliveredAlongside",
            delivery_var="deliveredAlongside",
            delivery_date_attr="alongsideDate",
            delivery_domain_comment="  // Delivery: seller places the goods alongside the nominated vessel (risk passes).",
            documents_domain_comment="  // Seller hands the buyer the usual proof that the goods were delivered alongside.",
            contract_params_tail=_F_PARAMS,
            point_phrase="alongside",
            export_before_phrase="they are placed alongside",
            deliver_place_phrase="alongside it",
            provide_docs_line2="",  # unused: FAS has no bill of lading
            has_carrier=False,
            has_bol=False,
            has_vessel_nomination=True,
            has_seller_carriage=False,
            has_insurance=False,
        )
    if c.code == "CFR":
        return Profile(
            term_type="C",
            domain_comment=[
                "  // CFR - Cost and Freight (Incoterms 2020), named port of destination.",
                "  // Seller delivers on board and bears cost (freight) to the destination port,",
                "  // but risk passes to the buyer when the goods are on board at shipment.",
            ],
            delivery_event="LoadedOnBoard",
            delivery_var="loadedOnBoard",
            delivery_date_attr="onBoardDate",
            delivery_domain_comment="  // Delivery: seller places the goods on board the vessel (risk passes on board).",
            documents_domain_comment="  // Seller tenders the buyer the bill of lading for the destination port.",
            contract_params_tail=_C_PARAMS,
            point_phrase="on board",
            export_before_phrase="they go on board",
            deliver_place_phrase="",  # unused: C-terms have no vessel nomination
            provide_docs_line2="  // tenders it to the buyer as the usual transport document.",
            has_carrier=True,
            has_bol=True,
            has_vessel_nomination=False,
            has_seller_carriage=True,
            has_insurance=False,
        )
    if c.code == "CIF":
        return Profile(
            term_type="C",
            domain_comment=[
                "  // CIF - Cost, Insurance and Freight (Incoterms 2020), named port of destination.",
                "  // Seller delivers on board and bears cost (freight + insurance) to the",
                "  // destination port; risk passes to the buyer when the goods are on board.",
            ],
            delivery_event="LoadedOnBoard",
            delivery_var="loadedOnBoard",
            delivery_date_attr="onBoardDate",
            delivery_domain_comment="  // Delivery: seller places the goods on board the vessel (risk passes on board).",
            documents_domain_comment="  // Seller tenders the buyer the bill of lading for the destination port.",
            contract_params_tail=_C_PARAMS + ", insuranceCover: String",
            point_phrase="on board",
            export_before_phrase="they go on board",
            deliver_place_phrase="",
            provide_docs_line2="  // tenders it to the buyer as the usual transport document.",
            has_carrier=True,
            has_bol=True,
            has_vessel_nomination=False,
            has_seller_carriage=True,
            has_insurance=True,
            insurance_cover=c.insurance_cover,
        )
    raise NotImplementedError(f"no profile for {c.code} yet")


# --- section emitters --------------------------------------------------------
# Each returns the section's lines (no trailing blank line); assemble() joins
# them with blank separators, matching the golden layout.


def emit_domain(c: RuleConfig) -> list[str]:
    p = c.profile
    L = [f"Domain {c.domain_name}"]
    L += p.domain_comment
    L += [
        "  Seller isA Role with name: String, org: String;",
        "  Buyer isA Role with name: String, org: String;",
    ]
    if p.has_carrier:
        carrier_comment = (
            "  // The carrier the seller contracts to carry the goods to the destination port; it issues the bill of lading."
            if p.term_type == "C"
            else "  // The carrier operates the vessel the buyer nominates; it issues the bill of lading."
        )
        L += [carrier_comment, "  Carrier isA Role thirdParty with name: String, org: String;"]
    L += [
        "  Currency isAn Enumeration(CAD, USD, EUR);",
        "  // The goods sold; owner defaults to the seller until delivery.",
        "  Goods isAn Asset with description: String, quantity: Number, owner: Seller;",
    ]
    if p.has_bol:
        L += [
            "  // The bill of lading: the transport document evidencing shipment on board.",
            "  BillOfLading isAn Asset with blNumber: String, owner: Carrier;",
        ]
    if p.has_vessel_nomination:
        L += [
            "  // Buyer nominates the vessel and gives notice (name, loading point, deadline).",
            "  VesselNominated isAn Event with Env vesselName: String, Env loadingPort: String, dueDate: Date, performer: Buyer, controller: Buyer;",
        ]
    L += [
        "  // Seller clears the goods for export.",
        "  ExportCleared isAn Event with performer: Seller, controller: Seller;",
    ]
    if p.has_seller_carriage:
        L += [
            "  // Seller contracts carriage to the named destination port (and pays the freight).",
            "  CarriageContracted isAn Event with destinationPort: String, Env carrierName: String, dueDate: Date, performer: Seller, controller: Seller;",
        ]
    if p.has_insurance:
        L += [
            "  // Seller takes out cargo insurance for the buyer's benefit (level recorded as data).",
            "  InsuranceObtained isAn Event with coverLevel: String, Env policyNumber: String, performer: Seller, controller: Seller;",
        ]
    L += [
        p.delivery_domain_comment,
        f"  {p.delivery_event} isAn Event with port: String, Env {p.delivery_date_attr}: Date, delDueDate: Date, performer: Seller, controller: Seller;",
    ]
    if p.has_bol:
        L += [
            "  // Carrier issues the bill of lading once the goods are on board.",
            "  BillOfLadingIssued isAn Event with Env blNumber: String, performer: Carrier, controller: Carrier;",
        ]
    L += [
        p.documents_domain_comment,
        "  DocumentsProvided isAn Event with performer: Seller, controller: Seller;",
        "  // Buyer takes delivery of the goods.",
        "  GoodsTakenOver isAn Event with performer: Buyer, controller: Buyer;",
        "  // Buyer pays the price.",
        "  Paid isAn Event with amount: Number, currency: Currency, from: Buyer, to: Seller, payDueDate: Date, performer: Buyer, controller: Buyer;",
        "endDomain",
    ]
    return L


def emit_contract_header(c: RuleConfig) -> list[str]:
    carrier = "buyerP: Buyer, carrierP: Carrier," if c.profile.has_carrier else "buyerP: Buyer,"
    return [
        f"Contract {c.code} (",
        f"  sellerP: Seller, {carrier}",
        "  goodsDesc: String, qty: Number, price: Number, curr: Currency,",
        c.profile.contract_params_tail,
        ")",
    ]


def emit_declarations(c: RuleConfig) -> list[str]:
    p = c.profile
    L = [
        "Declarations",
        "  seller: Seller with name := sellerP.name, org := sellerP.org;",
        "  buyer: Buyer with name := buyerP.name, org := buyerP.org;",
    ]
    if p.has_carrier:
        L += ["  carrier: Carrier with name := carrierP.name, org := carrierP.org;"]
    L += ["  goods: Goods with description := goodsDesc, quantity := qty, owner := seller;"]
    if p.has_bol:
        L += ['  billOfLading: BillOfLading with blNumber := "", owner := carrier;']
    if p.has_vessel_nomination:
        L += ["  vesselNominated: VesselNominated with dueDate := Date.add(effDate, noticeDays, days), performer := buyer, controller := buyer;"]
    L += ["  exportCleared: ExportCleared with performer := seller, controller := seller;"]
    if p.has_seller_carriage:
        L += ["  carriageContracted: CarriageContracted with destinationPort := portOfDestination, dueDate := Date.add(effDate, carriageDays, days), performer := seller, controller := seller;"]
    if p.has_insurance:
        L += ["  insuranceObtained: InsuranceObtained with coverLevel := insuranceCover, performer := seller, controller := seller;"]
    L += [
        f"  {p.delivery_var}: {p.delivery_event} with port := portOfShipment, delDueDate := Date.add(effDate, deliveryDays, days), performer := seller, controller := seller;",
    ]
    if p.has_bol:
        L += ["  billOfLadingIssued: BillOfLadingIssued with performer := carrier, controller := carrier;"]
    L += [
        "  documentsProvided: DocumentsProvided with performer := seller, controller := seller;",
        "  goodsTakenOver: GoodsTakenOver with performer := buyer, controller := buyer;",
        "  paid: Paid with amount := price, currency := curr, from := buyer, to := seller, payDueDate := Date.add(effDate, paymentDays, days), performer := buyer, controller := buyer;",
    ]
    return L


def emit_preconditions(c: RuleConfig) -> list[str]:
    return ["Preconditions", "  goods.quantity > 0;"]


def emit_obligations(c: RuleConfig) -> list[str]:
    p = c.profile
    L = [
        "Obligations",
        f"  // A7: the seller clears the goods for export before {p.export_before_phrase}.",
        f"  oExportClearance: O(seller, buyer, true, ShappensBefore(exportCleared, {p.delivery_var}));",
    ]
    if p.has_seller_carriage:
        L += [
            "  // A4: the seller contracts carriage to the named destination port, at its own cost, in time.",
            "  oContractCarriage: O(seller, buyer, true,",
            "              WhappensBefore(carriageContracted, carriageContracted.dueDate)",
            "              and carriageContracted.destinationPort == portOfDestination);",
        ]
    if p.has_insurance:
        L += [
            "  // A5: the seller takes out cargo insurance (min. ICC (C), 110% of price) for the buyer.",
            f"  oInsure: O(seller, buyer, true, ShappensBefore(insuranceObtained, {p.delivery_var}));",
        ]
    if p.has_vessel_nomination:
        L += [
            "  // A2 delivery: once the buyer has nominated the vessel, the seller must place",
            f"  // the goods {p.deliver_place_phrase}, at the named loading point, before the deadline.",
            "  oDeliver: Happens(vesselNominated) -> O(seller, buyer, true,",
            f"              WhappensBefore({p.delivery_var}, {p.delivery_var}.delDueDate)",
            f"              and {p.delivery_var}.port == vesselNominated.loadingPort);",
        ]
    else:  # C-term: unconditional delivery on board at the port of shipment
        L += [
            "  // A2 delivery: the seller places the goods on board the vessel at the port of",
            "  // shipment before the deadline; risk passes to the buyer on board.",
            "  oDeliver: O(seller, buyer, true,",
            f"              WhappensBefore({p.delivery_var}, {p.delivery_var}.delDueDate)",
            f"              and {p.delivery_var}.port == portOfShipment);",
        ]
    if p.has_bol:
        L += [
            "  // A6: after loading, the carrier issues the bill of lading and the seller",
            p.provide_docs_line2,
            f"  oProvideDocuments: Happens({p.delivery_var}) -> O(seller, buyer, true,",
            "              Happens(billOfLadingIssued) and Happens(documentsProvided));",
        ]
    else:
        L += [
            "  // A6: after delivery alongside, the seller provides the buyer with the usual",
            "  // proof that the goods were delivered alongside the vessel.",
            f"  oProvideDocuments: Happens({p.delivery_var}) -> O(seller, buyer, true,",
            "              Happens(documentsProvided));",
        ]
    if p.has_vessel_nomination:
        L += [
            "  // B7/B10: the buyer nominates the vessel and gives sufficient notice in time.",
            "  oNominateVessel: O(buyer, seller, true, WhappensBefore(vesselNominated, vesselNominated.dueDate));",
        ]
    L += [
        f"  // B2: the buyer takes delivery of the goods once they are {p.point_phrase}.",
        f"  oTakeDelivery: Happens({p.delivery_var}) -> O(buyer, seller, true, Happens(goodsTakenOver));",
    ]
    return L


def emit_surviving(c: RuleConfig) -> list[str]:
    p = c.profile
    evidence = "the bill of lading" if p.has_bol else "the usual proof of delivery"
    return [
        "Surviving Obligations",
        f"  // B1: the buyer must pay the price for goods delivered {p.point_phrase} and evidenced",
        f"  // by {evidence}; this survives termination of the contract.",
        f"  oPay: (Happens({p.delivery_var}) and Happens(documentsProvided)) -> Obligation(buyer, seller, true,",
        "              WhappensBefore(paid, paid.payDueDate) and paid.amount == price);",
    ]


def emit_powers(c: RuleConfig) -> list[str]:
    p = c.profile
    L = ["Powers"]
    if p.has_vessel_nomination:
        L += [
            "  // If the buyer fails to nominate the vessel in time, the seller may suspend delivery.",
            "  pSuspendDelivery: Happens(Violated(obligations.oNominateVessel)) ->",
            "              P(seller, buyer, true, Suspended(obligations.oDeliver)) with Controller seller;",
            "  // A late nomination during the suspension resumes the delivery obligation.",
            "  pResumeDelivery: HappensWithin(vesselNominated, Suspension(obligations.oDeliver)) ->",
            "              P(buyer, seller, true, Resumed(obligations.oDeliver));",
        ]
    if p.has_seller_carriage:
        L += [
            "  // If the seller fails to contract carriage to the destination, the buyer may terminate.",
            "  pTerminateNoCarriage: Happens(Violated(obligations.oContractCarriage)) -> P(buyer, seller, true, Terminated(self));",
        ]
    if p.has_insurance:
        L += [
            "  // If the seller fails to insure the cargo, the buyer may terminate.",
            "  pTerminateNoInsurance: Happens(Violated(obligations.oInsure)) -> P(buyer, seller, true, Terminated(self));",
        ]
    L += [
        f"  // If the seller fails to deliver {p.point_phrase}, the buyer may terminate the contract.",
        "  pTerminateByBuyer: Happens(Violated(obligations.oDeliver)) -> P(buyer, seller, true, Terminated(self));",
        "  // If the buyer fails to take delivery, the seller may terminate the contract.",
        "  pTerminateBySeller: Happens(Violated(obligations.oTakeDelivery)) -> P(seller, buyer, true, Terminated(self));",
    ]
    return L


def emit_acpolicy(c: RuleConfig) -> list[str]:
    p = c.profile
    L = [
        "ACPolicy with Controller seller",
        "  Rule1: Grant read To buyer On goods.description by seller;",
        "  Rule2: Grant read To buyer On obligations.oDeliver by seller;",
    ]
    n = 3
    if p.has_seller_carriage:
        L += [f"  Rule{n}: Grant read To buyer On carriageContracted by seller;"]
        n += 1
    if p.has_insurance:
        L += [f"  Rule{n}: Grant read To buyer On insuranceObtained by seller;"]
        n += 1
    if p.has_carrier:
        if not p.has_seller_carriage:
            # F-term with a carrier: the carrier reads the delivery event.
            L += [f"  Rule{n}: Grant read To carrier On {p.delivery_var} by seller;"]
            n += 1
        L += [
            f"  Rule{n}: Grant read To seller On billOfLadingIssued by carrier;",
            f"  Rule{n + 1}: Grant write To carrier On billOfLading.blNumber by seller;",
            f"  Rule{n + 2}: Grant write To buyer On powers.pTerminateByBuyer by seller;",
        ]
    else:
        # No carrier (FAS): buyer reads the delivery event and holds the power.
        L += [
            f"  Rule{n}: Grant read To buyer On {p.delivery_var} by seller;",
            f"  Rule{n + 1}: Grant write To buyer On powers.pTerminateByBuyer by seller;",
        ]
    return L


def emit_constraints(c: RuleConfig) -> list[str]:
    return ["Constraints", "  not(IsEqual(buyer, seller));"]


def assemble(c: RuleConfig) -> str:
    """Join sections in the grammar's required order, blank-line separated."""
    c.profile = profile_for(c)
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

    if args.stdout:
        code = args.stdout.upper()
        if code not in rules:
            return _err(f"unknown rule {code}")
        sys.stdout.write(assemble(rules[code]))
        return 0

    codes = [c.upper() for c in args.only.split(",")] if args.only else IMPLEMENTED
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
