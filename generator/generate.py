#!/usr/bin/env python3
"""Table-driven SymboleoAC generator for the Incoterms 2020 rules.

Reads the ICC allocation tables (``incoterms.data.yaml``) and emits one
``specs/<CODE>.symboleo`` per rule from a shared domain ontology + a library of
norm templates. The 11 specs are kept structurally parallel — they share the
vocabulary and the template *shapes* — while each declares only the
events/assets/norms that its Incoterms rule actually uses (faithful per-rule
modelling). The varying tokens live in a per-rule ``Profile``.

Two orthogonal axes drive the templates:
  * term_type — **E** (EXW: goods made available at the seller's premises,
    minimum seller obligation), **F** (buyer contracts carriage + nominates the
    vessel/carrier; oNominateX + suspend/resume powers), **C** (seller contracts
    carriage to destination; oContractCarriage + pTerminateNoCarriage; risk
    still passes at the origin delivery point while cost runs to destination),
    or **D** (delivery at destination; risk and cost pass together there).
    CIF/CIP add a seller insurance obligation (cover level is data only).
  * family — **sea** (vessel / port / on-board or alongside / bill of lading) vs
    **any_mode** (carrier / place / handover to the (first) carrier).

Implemented: all 11 rules. FOB was originally factored out of a hand-written
golden spec (reproduced byte-for-byte); roles later gained a `dept: String`
attribute required by the SymboleoAC access-control authenticate for on-chain
deployment (see deploy/README.md), so the specs are now defined purely by this
generator and pinned by the CI regeneration guard.

Usage:
    python generator/generate.py [--only FOB[,FCA,...]] [--out specs] [--check]
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
IMPLEMENTED = ["CFR", "CIF", "CIP", "CPT", "DAP", "DDP", "DPU", "EXW", "FAS", "FCA", "FOB"]


# --- mode vocabulary ---------------------------------------------------------
# The sea/any_mode families name the same roles differently. Keeping the tokens
# in one place lets the shared templates stay mode-agnostic.

def _sea_vocab() -> dict:
    return dict(
        transport_noun="vessel",
        nomination_event="VesselNominated",
        nomination_var="vesselNominated",
        nomination_name_attr="vesselName",
        nomination_place_attr="loadingPort",
        nominate_obl="oNominateVessel",
        nomination_place_word="loading point",
        delivery_place_attr="port",
        origin_param="portOfShipment",
        carriage_dest_attr="destinationPort",
        carriage_dest_word="destination port",
        dest_param="portOfDestination",
    )


def _any_vocab() -> dict:
    return dict(
        transport_noun="carrier",
        nomination_event="CarrierNominated",
        nomination_var="carrierNominated",
        nomination_name_attr="carrierName",
        nomination_place_attr="namedPlace",
        nominate_obl="oNominateCarrier",
        nomination_place_word="place",
        delivery_place_attr="place",
        origin_param="placeOfDelivery",
        carriage_dest_attr="destinationPlace",
        carriage_dest_word="destination",
        dest_param="placeOfDestination",
    )


# --- rule configuration ------------------------------------------------------


@dataclass
class Profile:
    """The per-rule tokens the shared templates vary on (faithful modelling)."""

    term_type: str               # "F" (buyer nominates) | "C" (seller carriage)
    family: str                  # "sea" | "any_mode"
    domain_comment: list[str]    # the lines under `Domain <x>`
    # Delivery event (where risk passes).
    delivery_event: str          # e.g. "LoadedOnBoard"
    delivery_var: str            # e.g. "loadedOnBoard"
    delivery_date_attr: str      # Env date attr, e.g. "onBoardDate"
    delivery_domain_comment: str
    documents_domain_comment: str
    contract_params_tail: str    # the places/deadlines param line
    # Short phrases woven into the norm comments.
    point_phrase: str            # "delivered <X>": "on board" | "to the carrier"
    take_phrase: str             # "once they are <X>": "on board" | "with the carrier"
    export_before_phrase: str    # "they go on board" | "they are handed to the carrier"
    deliver_place_phrase: str    # F-terms: "on board it" | "to the carrier"
    provide_docs_line2: str      # 2nd comment line of the carrier-document norm
    proof_docs_comment: list[str]  # comment for the proof-only (no carrier doc) norm
    c_deliver_comment: list[str]   # C-term oDeliver comment (2 lines)
    # Feature switches (approach A: declare only what the rule uses).
    has_carrier: bool            # Carrier role + carrier-issued bill of lading
    has_bol: bool
    has_insurance: bool
    # FCA only: the optional Incoterms 2020 on-board bill-of-lading mechanism
    # (A6/B6): if agreed, the buyer instructs its carrier - at the buyer's cost
    # and risk - to issue the seller an on-board B/L; the seller tenders it on.
    has_onboard_bl: bool = False
    # DPU only: the arrival event that must strictly precede the unloaded
    # delivery (DPU is the only rule where the seller unloads).
    has_arrival: bool = False
    has_export_clearance: bool = True   # False for EXW (buyer clears export)
    has_documents: bool = True          # False for EXW (no seller document norm)
    has_import_clearance: bool = False  # True for DDP (seller clears import)
    delivery_place_param: str = ""      # contract param the delivery place equals
    pay_second_conjunct: str = "documentsProvided"  # 2nd Happens() in oPay trigger
    pay_evidence: str = ""              # "evidenced by <X>" (default: per has_bol)
    insurance_cover: str | None = None
    # B3/B9(d) premature risk/cost transfer limbs modelled for this rule
    # (from incoterms.data.yaml b3_triggers; see the key's comment there).
    b3_triggers: list[str] = field(default_factory=list)
    # ICC request-triggered assistance topics per direction (yaml `assistance`).
    assist_to_buyer: list[str] = field(default_factory=list)
    assist_to_seller: list[str] = field(default_factory=list)
    # B7 buyer-side clearance (Wave 2d): every rule whose import clearance the
    # ICC table assigns to the buyer gets a first-class buyer obligation
    # (transit + import); EXW's buyer additionally clears export (see
    # has_buyer_full_clearance).
    buyer_import_clearance: bool = False
    insurance_cover_phrase: str = ""   # e.g. "ICC (C)" / "ICC (A)" (CIF/CIP)
    # Mode vocabulary (spread from _sea_vocab / _any_vocab).
    transport_noun: str = ""
    nomination_event: str = ""
    nomination_var: str = ""
    nomination_name_attr: str = ""
    nomination_place_attr: str = ""
    nominate_obl: str = ""
    nomination_place_word: str = ""
    delivery_place_attr: str = ""
    origin_param: str = ""
    carriage_dest_attr: str = ""
    carriage_dest_word: str = ""
    dest_param: str = ""

    @property
    def has_nomination(self) -> bool:
        return self.term_type == "F"

    @property
    def has_string_sale(self) -> bool:
        # A2 of every rule except EXW lets the seller alternatively "procure
        # goods so delivered" (string sales, common in commodity chains).
        return self.term_type != "E"

    @property
    def has_failure_costs(self) -> bool:
        return bool(self.b3_triggers)

    @property
    def has_buyer_import_clearance(self) -> bool:
        return self.buyer_import_clearance

    @property
    def has_buyer_full_clearance(self) -> bool:
        # EXW: the buyer carries out and pays for ALL clearance formalities -
        # export, transit, and import (the seller only assists on request).
        return self.term_type == "E"

    @property
    def has_security_compliance(self) -> bool:
        # A4 (2020): every rule except EXW puts a transport-security compliance
        # duty on the seller - up to delivery (E/F) or for the transport to the
        # destination (C/D).
        return self.term_type != "E"

    @property
    def has_schedule_notice(self) -> bool:
        # Non-F rules carry the conditional B10 notice ("whenever it is agreed
        # that the buyer is entitled to determine the time and/or point ...");
        # for the F-terms the nomination obligation IS the B10 notice.
        return not self.has_nomination

    @property
    def third_party_failure(self) -> tuple[str, str] | None:
        # (EventType, varName) of the modelled third-party failure event.
        if "vessel_failed" in self.b3_triggers:
            return ("VesselFailedToLoad", "vesselFailedToLoad")
        if "carrier_failed" in self.b3_triggers:
            return ("CarrierFailedToTakeCharge", "carrierFailedToTakeCharge")
        return None

    @property
    def has_seller_carriage(self) -> bool:
        # C-terms (carriage to destination) and D-terms (delivery at destination
        # requires it) both put carriage on the seller.
        return self.term_type in ("C", "D")

    @property
    def delivers_at_destination(self) -> bool:
        return self.term_type == "D"


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
    b3_triggers: list[str] = field(default_factory=list)
    assistance: dict = field(default_factory=dict)
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
            b3_triggers=list(row.get("b3_triggers") or []),
            assistance=dict(row.get("assistance") or {}),
        )
    return rules


def _params_tail(term: str, vocab: dict, insurance: bool, buyer_import: bool = False) -> str:
    # noticeDays: F-terms use it for the nomination deadline; the other rules
    # (Wave 2) use it for the conditional B10 schedule notice (oNotifySchedule).
    # importDays: deadline of the buyer's clearance obligation (all rules whose
    # import clearance the ICC table assigns to the buyer; for EXW it bounds
    # the buyer's full export/transit/import clearance).
    # reimburseDays (L4): every rule has at least one assistance channel
    # (to-buyer except DDP, to-seller except EXW), so the reimbursement
    # deadline param -- "within reimburseDays of the assistance provided" -- is
    # universal.
    if term == "F":
        tail = f"  {vocab['origin_param']}: String, effDate: Date, noticeDays: Number, importDays: Number, deliveryDays: Number, paymentDays: Number, reimburseDays: Number, assistDays: Number"
    elif term == "C":
        tail = f"  {vocab['origin_param']}: String, {vocab['dest_param']}: String, effDate: Date, noticeDays: Number, carriageDays: Number, importDays: Number, deliveryDays: Number, paymentDays: Number, reimburseDays: Number, assistDays: Number"
    elif term == "D":
        # Delivery is at destination; there is no separate origin place param.
        days = "carriageDays: Number, importDays: Number, deliveryDays: Number" if buyer_import else "carriageDays: Number, deliveryDays: Number"
        tail = f"  {vocab['dest_param']}: String, effDate: Date, noticeDays: Number, {days}, paymentDays: Number, reimburseDays: Number, assistDays: Number"
    else:  # "E": EXW — goods made available at the seller's premises.
        tail = f"  {vocab['origin_param']}: String, effDate: Date, noticeDays: Number, importDays: Number, deliveryDays: Number, paymentDays: Number, reimburseDays: Number, assistDays: Number"
    # L2: the ICC cover clause is no longer a display-string parameter; the
    # obtained cover is an Env attribute on InsuranceObtained (coverLevel:
    # ICCClause) and the rule's minimum is a fixed enum literal in oInsure.
    return tail


def _delivery_place_param(term: str, vocab: dict) -> str:
    # Where the delivery event happens: origin for F/C/E, destination for D.
    return vocab["dest_param"] if term == "D" else vocab["origin_param"]


# Per-rule specifics (everything not fixed by term_type/family/vocab).
_SPECIFICS = {
    "FOB": dict(
        term_type="F", family="sea",
        domain_comment=[
            "  // FOB - Free on Board (Incoterms 2020), named port of shipment.",
            "  // Seller bears cost and risk up to the moment the goods are on board the",
            "  // vessel nominated by the buyer; risk then passes to the buyer.",
        ],
        delivery_event="LoadedOnBoard", delivery_var="loadedOnBoard", delivery_date_attr="onBoardDate",
        delivery_domain_comment="  // Delivery: seller places the goods on board the nominated vessel (risk passes).",
        documents_domain_comment="  // Seller hands the buyer the usual proof of delivery (the bill of lading).",
        point_phrase="on board", take_phrase="on board",
        export_before_phrase="they go on board", deliver_place_phrase="on board it",
        provide_docs_line2="  // provides the buyer with that proof of delivery.",
        proof_docs_comment=[], c_deliver_comment=[],
        has_carrier=True, has_bol=True, has_insurance=False,
    ),
    "FAS": dict(
        term_type="F", family="sea",
        domain_comment=[
            "  // FAS - Free Alongside Ship (Incoterms 2020), named port of shipment.",
            "  // Seller bears cost and risk up to the moment the goods are placed alongside",
            "  // the vessel nominated by the buyer; risk then passes to the buyer.",
        ],
        delivery_event="DeliveredAlongside", delivery_var="deliveredAlongside", delivery_date_attr="alongsideDate",
        delivery_domain_comment="  // Delivery: seller places the goods alongside the nominated vessel (risk passes).",
        documents_domain_comment="  // Seller hands the buyer the usual proof that the goods were delivered alongside.",
        point_phrase="alongside", take_phrase="alongside",
        export_before_phrase="they are placed alongside", deliver_place_phrase="alongside it",
        provide_docs_line2="",
        proof_docs_comment=[
            "  // A6: after delivery alongside, the seller provides the buyer with the usual",
            "  // proof that the goods were delivered alongside the vessel.",
        ],
        c_deliver_comment=[],
        has_carrier=False, has_bol=False, has_insurance=False,
    ),
    "CFR": dict(
        term_type="C", family="sea",
        domain_comment=[
            "  // CFR - Cost and Freight (Incoterms 2020), named port of destination.",
            "  // Seller delivers on board and bears cost (freight) to the destination port,",
            "  // but risk passes to the buyer when the goods are on board at shipment.",
        ],
        delivery_event="LoadedOnBoard", delivery_var="loadedOnBoard", delivery_date_attr="onBoardDate",
        delivery_domain_comment="  // Delivery: seller places the goods on board the vessel (risk passes on board).",
        documents_domain_comment="  // Seller tenders the buyer the bill of lading for the destination port.",
        point_phrase="on board", take_phrase="on board",
        export_before_phrase="they go on board", deliver_place_phrase="",
        provide_docs_line2="  // tenders it to the buyer as the usual transport document.",
        proof_docs_comment=[],
        c_deliver_comment=[
            "  // A2 delivery: the seller places the goods on board the vessel at the port of",
            "  // shipment before the deadline; risk passes to the buyer on board.",
        ],
        has_carrier=True, has_bol=True, has_insurance=False,
    ),
    "CIF": dict(
        term_type="C", family="sea",
        domain_comment=[
            "  // CIF - Cost, Insurance and Freight (Incoterms 2020), named port of destination.",
            "  // Seller delivers on board and bears cost (freight + insurance) to the",
            "  // destination port; risk passes to the buyer when the goods are on board.",
        ],
        delivery_event="LoadedOnBoard", delivery_var="loadedOnBoard", delivery_date_attr="onBoardDate",
        delivery_domain_comment="  // Delivery: seller places the goods on board the vessel (risk passes on board).",
        documents_domain_comment="  // Seller tenders the buyer the bill of lading for the destination port.",
        point_phrase="on board", take_phrase="on board",
        export_before_phrase="they go on board", deliver_place_phrase="",
        provide_docs_line2="  // tenders it to the buyer as the usual transport document.",
        proof_docs_comment=[],
        c_deliver_comment=[
            "  // A2 delivery: the seller places the goods on board the vessel at the port of",
            "  // shipment before the deadline; risk passes to the buyer on board.",
        ],
        has_carrier=True, has_bol=True, has_insurance=True, insurance_cover_phrase="ICC (C)",
    ),
    "FCA": dict(
        term_type="F", family="any_mode",
        domain_comment=[
            "  // FCA - Free Carrier (Incoterms 2020), named place of delivery; any transport mode.",
            "  // Seller delivers by handing the goods to the carrier nominated by the buyer;",
            "  // risk then passes to the buyer at that handover.",
        ],
        delivery_event="HandedToCarrier", delivery_var="handedToCarrier", delivery_date_attr="handoverDate",
        delivery_domain_comment="  // Delivery: seller hands the goods to the buyer's carrier at the named place (risk passes).",
        documents_domain_comment="  // Seller hands the buyer the usual proof of delivery to the carrier.",
        point_phrase="to the carrier", take_phrase="with the carrier",
        export_before_phrase="they are handed to the carrier", deliver_place_phrase="to the carrier",
        provide_docs_line2="",
        proof_docs_comment=[
            "  // A6: after handing the goods to the carrier, the seller provides the buyer",
            "  // with the usual proof that the goods were delivered.",
        ],
        c_deliver_comment=[],
        has_carrier=False, has_bol=False, has_insurance=False, has_onboard_bl=True,
    ),
    "CPT": dict(
        term_type="C", family="any_mode",
        domain_comment=[
            "  // CPT - Carriage Paid To (Incoterms 2020), named place of destination; any mode.",
            "  // Seller contracts carriage to destination and hands the goods to the first",
            "  // carrier; risk passes at that handover, while cost runs to the destination.",
        ],
        delivery_event="HandedToFirstCarrier", delivery_var="handedToFirstCarrier", delivery_date_attr="handoverDate",
        delivery_domain_comment="  // Delivery: seller hands the goods to the first carrier it contracted (risk passes on handover).",
        documents_domain_comment="  // Seller tenders the buyer the usual transport document for the carriage.",
        point_phrase="to the carrier", take_phrase="with the carrier",
        export_before_phrase="they are handed to the carrier", deliver_place_phrase="",
        provide_docs_line2="",
        proof_docs_comment=[
            "  // A6: the seller provides the buyer with the usual transport document for the",
            "  // carriage it has contracted to the destination.",
        ],
        c_deliver_comment=[
            "  // A2 delivery: the seller hands the goods to the first carrier at the named",
            "  // place of delivery before the deadline; risk passes to the buyer on handover.",
        ],
        has_carrier=False, has_bol=False, has_insurance=False,
    ),
    "CIP": dict(
        term_type="C", family="any_mode",
        domain_comment=[
            "  // CIP - Carriage and Insurance Paid To (Incoterms 2020), named destination; any mode.",
            "  // Seller contracts carriage + insurance to destination and hands to the first",
            "  // carrier; risk passes at handover, while cost (incl. insurance) runs onward.",
        ],
        delivery_event="HandedToFirstCarrier", delivery_var="handedToFirstCarrier", delivery_date_attr="handoverDate",
        delivery_domain_comment="  // Delivery: seller hands the goods to the first carrier it contracted (risk passes on handover).",
        documents_domain_comment="  // Seller tenders the buyer the usual transport document for the carriage.",
        point_phrase="to the carrier", take_phrase="with the carrier",
        export_before_phrase="they are handed to the carrier", deliver_place_phrase="",
        provide_docs_line2="",
        proof_docs_comment=[
            "  // A6: the seller provides the buyer with the usual transport document for the",
            "  // carriage it has contracted to the destination.",
        ],
        c_deliver_comment=[
            "  // A2 delivery: the seller hands the goods to the first carrier at the named",
            "  // place of delivery before the deadline; risk passes to the buyer on handover.",
        ],
        has_carrier=False, has_bol=False, has_insurance=True, insurance_cover_phrase="ICC (A)",
    ),
    "DAP": dict(
        term_type="D", family="any_mode",
        domain_comment=[
            "  // DAP - Delivered At Place (Incoterms 2020), named place of destination; any mode.",
            "  // Seller bears cost and risk all the way to destination and places the goods",
            "  // at the buyer's disposal there, ready for unloading; risk passes at destination.",
        ],
        delivery_event="MadeAvailableAtDestination", delivery_var="madeAvailable", delivery_date_attr="arrivalDate",
        delivery_domain_comment="  // Delivery: seller makes the goods available at the destination, ready for unloading (risk passes).",
        documents_domain_comment="  // Seller gives the buyer the document/notice letting it take delivery at destination.",
        point_phrase="at the destination", take_phrase="at the destination",
        export_before_phrase="they are dispatched", deliver_place_phrase="",
        provide_docs_line2="",
        proof_docs_comment=[
            "  // A6: the seller provides the buyer with the document/notice that lets it take",
            "  // delivery of the goods at the named place of destination.",
        ],
        c_deliver_comment=[
            "  // A2 delivery: the seller places the goods at the buyer's disposal, ready for",
            "  // unloading, at the named place of destination before the deadline; risk passes there.",
        ],
        has_carrier=False, has_bol=False, has_insurance=False,
    ),
    "DPU": dict(
        term_type="D", family="any_mode",
        domain_comment=[
            "  // DPU - Delivered at Place Unloaded (Incoterms 2020), named destination; any mode.",
            "  // Seller bears cost and risk to destination and, uniquely, unloads the goods",
            "  // there before placing them at the buyer's disposal; risk passes once unloaded.",
        ],
        delivery_event="UnloadedAtDestination", delivery_var="unloadedAtDestination", delivery_date_attr="unloadDate",
        delivery_domain_comment="  // Delivery: seller unloads the goods and makes them available at the destination (risk passes).",
        documents_domain_comment="  // Seller gives the buyer the document/notice letting it take delivery at destination.",
        point_phrase="at the destination", take_phrase="at the destination",
        export_before_phrase="they are dispatched", deliver_place_phrase="",
        provide_docs_line2="",
        proof_docs_comment=[
            "  // A6: the seller provides the buyer with the document/notice that lets it take",
            "  // delivery of the goods at the named place of destination.",
        ],
        c_deliver_comment=[
            "  // A2 delivery: the seller unloads the goods from the arriving means of transport",
            "  // and places them at the buyer's disposal at the destination before the deadline.",
        ],
        has_carrier=False, has_bol=False, has_insurance=False, has_arrival=True,
    ),
    "DDP": dict(
        term_type="D", family="any_mode",
        domain_comment=[
            "  // DDP - Delivered Duty Paid (Incoterms 2020), named place of destination; any mode.",
            "  // Maximum seller obligation: cost and risk to destination AND import clearance",
            "  // (duties paid); the goods are placed at the buyer's disposal, cleared, at destination.",
        ],
        delivery_event="MadeAvailableAtDestination", delivery_var="madeAvailable", delivery_date_attr="arrivalDate",
        delivery_domain_comment="  // Delivery: seller makes the import-cleared goods available at the destination (risk passes).",
        documents_domain_comment="  // Seller gives the buyer the document/notice letting it take delivery at destination.",
        point_phrase="at the destination", take_phrase="at the destination",
        export_before_phrase="they are dispatched", deliver_place_phrase="",
        provide_docs_line2="",
        proof_docs_comment=[
            "  // A6: the seller provides the buyer with the document/notice that lets it take",
            "  // delivery of the goods at the named place of destination.",
        ],
        c_deliver_comment=[
            "  // A2 delivery: the seller places the goods, cleared for import, at the buyer's",
            "  // disposal at the named place of destination before the deadline; risk passes there.",
        ],
        has_carrier=False, has_bol=False, has_insurance=False, has_import_clearance=True,
    ),
    "EXW": dict(
        term_type="E", family="any_mode",
        domain_comment=[
            "  // EXW - Ex Works (Incoterms 2020), named place (the seller's premises); any mode.",
            "  // Minimum seller obligation: the goods are placed at the buyer's disposal at the",
            "  // seller's premises; risk passes there and the buyer bears everything onward.",
        ],
        delivery_event="GoodsMadeAvailable", delivery_var="goodsMadeAvailable", delivery_date_attr="availableDate",
        delivery_domain_comment="  // Delivery: seller makes the goods available at its premises (risk passes).",
        documents_domain_comment="",
        point_phrase="at the seller's premises", take_phrase="at the seller's premises",
        export_before_phrase="", deliver_place_phrase="",
        provide_docs_line2="",
        proof_docs_comment=[],
        c_deliver_comment=[
            "  // A2 delivery: the seller places the goods at the buyer's disposal at its own",
            "  // premises (the named place) before the deadline; risk passes to the buyer there.",
        ],
        has_carrier=False, has_bol=False, has_insurance=False,
        has_export_clearance=False, has_documents=False,
        pay_second_conjunct="goodsTakenOver", pay_evidence="their collection",
    ),
}


def profile_for(c: RuleConfig) -> Profile:
    spec = _SPECIFICS.get(c.code)
    if spec is None:
        raise NotImplementedError(f"no profile for {c.code} yet")
    vocab = _sea_vocab() if spec["family"] == "sea" else _any_vocab()
    # Buyer-side clearance obligation: every non-EXW rule whose import
    # clearance the ICC table assigns to the buyer (EXW's buyer clears
    # everything and gets the full-clearance obligation instead).
    buyer_import = c.import_clearance == "buyer" and spec["term_type"] != "E"
    tail = _params_tail(spec["term_type"], vocab, spec["has_insurance"], buyer_import)
    cover = c.insurance_cover if spec["has_insurance"] else None
    dpp = _delivery_place_param(spec["term_type"], vocab)
    return Profile(contract_params_tail=tail, insurance_cover=cover,
                   delivery_place_param=dpp, b3_triggers=list(c.b3_triggers),
                   assist_to_buyer=list(c.assistance.get("to_buyer") or []),
                   assist_to_seller=list(c.assistance.get("to_seller") or []),
                   buyer_import_clearance=buyer_import,
                   **spec, **vocab)


# --- section emitters --------------------------------------------------------
# Each returns the section's lines (no trailing blank line); assemble() joins
# them with blank separators, matching the golden layout.


def emit_domain(c: RuleConfig) -> list[str]:
    p = c.profile
    L = [f"Domain {c.domain_name}"]
    L += p.domain_comment
    L += [
        "  Seller isA Role with name: String, org: String, dept: String;",
        "  Buyer isA Role with name: String, org: String, dept: String;",
    ]
    if p.has_carrier:
        carrier_comment = (
            "  // The carrier the seller contracts to carry the goods to the destination port; it issues the bill of lading."
            if p.has_seller_carriage
            else "  // The carrier operates the vessel the buyer nominates; it issues the bill of lading."
        )
        L += [carrier_comment, "  Carrier isA Role thirdParty with name: String, org: String, dept: String;"]
    elif p.has_onboard_bl:
        L += [
            "  // The carrier the buyer nominates; if the on-board B/L mechanism is agreed,",
            "  // it issues the seller a transport document with an on-board notation.",
            "  Carrier isA Role thirdParty with name: String, org: String, dept: String;",
        ]
    L += [
        "  Currency isAn Enumeration(CAD, USD, EUR);",
        "  // The goods sold; owner defaults to the seller until delivery.",
        "  Goods isAn Asset with description: String, quantity: Number, owner: Seller;",
    ]
    if p.has_bol:
        L += [
            "  // The bill of lading: the transport document evidencing shipment on board.",
            "  // The carrier issues it TO the shipper (Hague-Visby art. III(3)), so the",
            "  // seller is the document's owner/holder: it authorizes the carrier to fill",
            "  // in the number at issuance and endorses the document to the buyer (the",
            "  // buyer's transfer grant). The carrier's own authority is over the",
            "  // issuance event, of which it is performer and controller.",
            "  BillOfLading isAn Asset with blNumber: String, owner: Seller;",
        ]
    if p.has_nomination:
        L += [
            f"  // Buyer nominates the {p.transport_noun} and gives notice (name, {p.nomination_place_word},",
            "  // transport-security requirements, deadline) - the typed B10 content.",
            f"  {p.nomination_event} isAn Event with Env {p.nomination_name_attr}: String, Env {p.nomination_place_attr}: String, Env securityRequirements: String, dueDate: Date, performer: Buyer, controller: Buyer;",
        ]
    if p.has_schedule_notice:
        L += [
            "  // B10 (conditional): the parties may agree that the buyer is entitled to",
            "  // determine the time and/or point of delivery (recorded by ScheduleRightAgreed);",
            "  // the buyer must then give sufficient notice in time.",
            "  ScheduleRightAgreed isAn Event with performer: Buyer, controller: Buyer;",
            "  ScheduleNotified isAn Event with Env chosenDate: Date, Env chosenPoint: String, Env securityRequirements: String, dueDate: Date, performer: Buyer, controller: Buyer;",
        ]
    if p.third_party_failure:
        ev, _ = p.third_party_failure
        failure_comment = (
            "  // B3: the nominated vessel fails to arrive on time, fails to take the goods,"
            "\n  // or closes for cargo earlier than notified; the buyer answers for its nominee."
            if ev == "VesselFailedToLoad" else
            "  // B3(a): the carrier nominated by the buyer fails to take the goods into"
            "\n  // its charge; the buyer answers for its nominee."
        )
        L += [
            failure_comment,
            f"  {ev} isAn Event with Env reason: String, performer: Buyer, controller: Buyer;",
        ]
    L += [
        "  // A1: the seller provides the commercial invoice (and any other evidence of",
        "  // conformity the contract of sale requires) in conformity with the contract.",
        "  InvoiceProvided isAn Event with performer: Seller, controller: Seller;",
        "  // A8: the seller checks (quality, weight, count), packages and marks the goods",
        "  // appropriately for transport, at its own cost - unless unpackaged carriage is",
        "  // usual for the trade or the parties agreed specific packaging requirements",
        "  // (the two ICC defeaters are recorded here, not modelled).",
        "  PackagedAndMarked isAn Event with performer: Seller, controller: Seller;",
    ]
    if p.has_export_clearance:
        L += [
            "  // Seller clears the goods for export.",
            "  ExportCleared isAn Event with performer: Seller, controller: Seller;",
        ]
    if p.has_seller_carriage:
        L += [
            f"  // Seller contracts carriage to the named {p.carriage_dest_word} (and pays the freight).",
            f"  CarriageContracted isAn Event with {p.carriage_dest_attr}: String, Env carrierName: String, dueDate: Date, performer: Seller, controller: Seller;",
        ]
    if p.has_import_clearance:
        L += [
            "  // Seller also clears the goods for import at the destination (duties paid).",
            "  ImportCleared isAn Event with performer: Seller, controller: Seller;",
        ]
    if p.has_buyer_import_clearance:
        L += [
            "  // B7 ('where applicable'): the buyer carries out and pays for transit and",
            "  // import clearance formalities - licences, security clearance, pre-shipment",
            "  // inspection, duties - in time for delivery/receipt.",
            "  ImportClearedByBuyer isAn Event with dueDate: Date, performer: Buyer, controller: Buyer;",
        ]
    if p.has_buyer_full_clearance:
        L += [
            "  // B7 EXW ('where applicable'): the buyer carries out and pays for ALL",
            "  // clearance formalities - export, transit AND import (the seller only",
            "  // assists on request; see the assistance channel).",
            "  ClearedByBuyer isAn Event with dueDate: Date, performer: Buyer, controller: Buyer;",
        ]
    if p.has_security_compliance:
        L += [
            "  // A4 (2020): the seller complies with transport-related security requirements",
            f"  // {'up to delivery' if p.term_type == 'F' else 'for the transport to the destination'}.",
            "  SecurityComplied isAn Event with performer: Seller, controller: Seller;",
        ]
    if p.has_insurance:
        L += [
            "  // A5: seller takes out cargo insurance for the buyer's benefit. The ICC",
            "  // cover clauses form an ORDERED enumeration (C < B < A: minimum to broadest);",
            "  // oInsure requires the obtained cover to be at least the rule's minimum, plus",
            "  // the minimum insured amount (110% of the price) and the contract currency.",
            "  ICCClause isAn Enumeration(C, B, A);",
            "  InsuranceObtained isAn Event with Env coverLevel: ICCClause, Env policyNumber: String, Env insuredAmount: Number, Env insuredCurrency: Currency, performer: Seller, controller: Seller;",
            "  // A5: the seller provides the buyer with the policy/certificate or other",
            "  // evidence of the insurance cover.",
            "  InsuranceDocProvided isAn Event with performer: Seller, controller: Seller;",
            "  // A5/B5 (conditional): additional War/Strikes cover at the buyer's request",
            "  // and cost, subject to the buyer supplying the information the seller needs",
            "  // ('if procurable' - the feasibility escape is recorded, not modelled).",
            "  AdditionalCoverRequested isAn Event with Env clauses: String, performer: Buyer, controller: Buyer;",
            "  AdditionalCoverInfoGiven isAn Event with performer: Buyer, controller: Buyer;",
            "  AdditionalCoverObtained isAn Event with Env policyNumber: String, performer: Seller, controller: Seller;",
            "  AdditionalCoverPaid isAn Event with Env amount: Number, performer: Buyer, controller: Buyer;",
        ]
    if p.has_arrival:
        L += [
            "  // DPU only: the goods arrive at the destination on the means of transport;",
            "  // the seller must then unload them - delivery IS the unloaded state.",
            "  ArrivedAtDestination isAn Event with performer: Seller, controller: Seller;",
        ]
    L += [
        p.delivery_domain_comment,
        f"  {p.delivery_event} isAn Event with {p.delivery_place_attr}: String, Env {p.delivery_date_attr}: Date, delDueDate: Date, performer: Seller, controller: Seller;",
    ]
    if p.has_string_sale:
        L += [
            "  // A2 alternative performance: the seller may instead procure goods already",
            "  // so delivered (string sales, common in commodity chains).",
            "  ProcuredSoDelivered isAn Event with performer: Seller, controller: Seller;",
        ]
    if p.has_bol:
        L += [
            "  // Carrier issues the bill of lading once the goods are on board. A6 content",
            "  // requirements: negotiable form implies a full set of originals (customarily",
            "  // three); the issuance must fall within the shipment period (see oProvideDocuments).",
            "  BillOfLadingIssued isAn Event with Env blNumber: String, Env negotiable: Boolean, Env originalsCount: Number, performer: Carrier, controller: Carrier;",
        ]
    if p.has_documents:
        L += [
            p.documents_domain_comment,
            "  // The Env conforming flag records whether the tendered documents are in",
            "  // conformity with the contract (B6: the buyer must accept them iff they are).",
            "  DocumentsProvided isAn Event with Env conforming: Boolean, performer: Seller, controller: Seller;",
        ]
    if p.has_onboard_bl:
        L += [
            "  // FCA A6/B6 optional mechanism (new in Incoterms 2020): if the parties have",
            "  // agreed (recorded by OnBoardBLAgreed), the buyer must instruct its carrier -",
            "  // at the buyer's cost and risk - to issue the seller a bill of lading with an",
            "  // on-board notation; the seller must then tender that document to the buyer.",
            "  // The carrier is not bound by the sale contract and may decline to issue.",
            "  OnBoardBLAgreed isAn Event with performer: Buyer, controller: Buyer;",
            "  BLInstructionGiven isAn Event with performer: Buyer, controller: Buyer;",
            "  OnBoardBLIssued isAn Event with Env blNumber: String, performer: Carrier, controller: Carrier;",
            "  OnBoardBLForwarded isAn Event with performer: Seller, controller: Seller;",
        ]
    L += [
        "  // A10: the seller gives the buyer the notice it needs to receive the goods -",
        "  // for the F-terms a dual notice: that the goods have been delivered, or that",
        "  // the nominated vessel/carrier failed to take them within the time agreed.",
        "  DeliveryNoticeGiven isAn Event with Env subject: String, performer: Seller, controller: Seller;",
        "  // Buyer takes delivery of the goods.",
        "  GoodsTakenOver isAn Event with performer: Buyer, controller: Buyer;",
    ]
    if p.assist_to_buyer:
        L += [
            "  // Request-triggered assistance channel, seller -> buyer (ICC pattern: 'at the",
            "  // buyer's request, risk and cost'; per-article topics at the obligation).",
            "  AssistanceToBuyerRequested isAn Event with Env topic: String, performer: Buyer, controller: Buyer;",
            "  AssistanceToBuyerProvided isAn Event with Env topic: String, performer: Seller, controller: Seller;",
            "  AssistanceToBuyerReimbursed isAn Event with Env amount: Number, performer: Buyer, controller: Buyer;",
        ]
    if p.assist_to_seller:
        L += [
            "  // Request-triggered assistance channel, buyer -> seller (ICC pattern: 'at the",
            "  // seller's request, risk and cost'; per-article topics at the obligation).",
            "  AssistanceToSellerRequested isAn Event with Env topic: String, performer: Seller, controller: Seller;",
            "  AssistanceToSellerProvided isAn Event with Env topic: String, performer: Buyer, controller: Buyer;",
            "  AssistanceToSellerReimbursed isAn Event with Env amount: Number, performer: Seller, controller: Seller;",
        ]
    if p.has_failure_costs:
        L += [
            "  // The goods are clearly identified (appropriated) as the contract goods -",
            "  // the ICC proviso guarding every premature risk/cost transfer (B3/B9).",
            "  GoodsIdentified isAn Event with performer: Seller, controller: Seller;",
            "  // B9(d): the buyer bears the additional costs caused by its (or its nominee's) failure.",
            "  AdditionalCostsPaid isAn Event with Env amount: Number, performer: Buyer, controller: Buyer;",
        ]
    L += [
        "  // Buyer pays the price.",
        "  Paid isAn Event with amount: Number, currency: Currency, from: Buyer, to: Seller, payDueDate: Date, performer: Buyer, controller: Buyer;",
        "endDomain",
    ]
    return L


def emit_contract_header(c: RuleConfig) -> list[str]:
    carrier = "buyerP: Buyer, carrierP: Carrier," if (c.profile.has_carrier or c.profile.has_onboard_bl) else "buyerP: Buyer,"
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
        "  seller: Seller with name := sellerP.name, org := sellerP.org, dept := sellerP.dept;",
        "  buyer: Buyer with name := buyerP.name, org := buyerP.org, dept := buyerP.dept;",
    ]
    if p.has_carrier or p.has_onboard_bl:
        L += ["  carrier: Carrier with name := carrierP.name, org := carrierP.org, dept := carrierP.dept;"]
    L += ["  goods: Goods with description := goodsDesc, quantity := qty, owner := seller;"]
    if p.has_bol:
        L += ['  billOfLading: BillOfLading with blNumber := "", owner := seller;']
    if p.has_nomination:
        L += [f"  {p.nomination_var}: {p.nomination_event} with dueDate := Date.add(effDate, noticeDays, days), performer := buyer, controller := buyer;"]
    if p.has_schedule_notice:
        L += [
            "  scheduleRightAgreed: ScheduleRightAgreed with performer := buyer, controller := buyer;",
            "  scheduleNotified: ScheduleNotified with dueDate := Date.add(effDate, noticeDays, days), performer := buyer, controller := buyer;",
        ]
    if p.third_party_failure:
        ev, var = p.third_party_failure
        L += [f"  {var}: {ev} with performer := buyer, controller := buyer;"]
    L += [
        "  invoiceProvided: InvoiceProvided with performer := seller, controller := seller;",
        "  packagedAndMarked: PackagedAndMarked with performer := seller, controller := seller;",
    ]
    if p.has_export_clearance:
        L += ["  exportCleared: ExportCleared with performer := seller, controller := seller;"]
    if p.has_seller_carriage:
        L += [f"  carriageContracted: CarriageContracted with {p.carriage_dest_attr} := {p.dest_param}, dueDate := Date.add(effDate, carriageDays, days), performer := seller, controller := seller;"]
    if p.has_import_clearance:
        L += ["  importCleared: ImportCleared with performer := seller, controller := seller;"]
    if p.has_buyer_import_clearance:
        L += ["  importClearedByBuyer: ImportClearedByBuyer with dueDate := Date.add(effDate, importDays, days), performer := buyer, controller := buyer;"]
    if p.has_buyer_full_clearance:
        L += ["  clearedByBuyer: ClearedByBuyer with dueDate := Date.add(effDate, importDays, days), performer := buyer, controller := buyer;"]
    if p.has_security_compliance:
        L += ["  securityComplied: SecurityComplied with performer := seller, controller := seller;"]
    if p.has_insurance:
        L += [
            "  insuranceObtained: InsuranceObtained with performer := seller, controller := seller;",
            "  insuranceDocProvided: InsuranceDocProvided with performer := seller, controller := seller;",
            "  additionalCoverRequested: AdditionalCoverRequested with performer := buyer, controller := buyer;",
            "  additionalCoverInfoGiven: AdditionalCoverInfoGiven with performer := buyer, controller := buyer;",
            "  additionalCoverObtained: AdditionalCoverObtained with performer := seller, controller := seller;",
            "  additionalCoverPaid: AdditionalCoverPaid with performer := buyer, controller := buyer;",
        ]
    if p.has_arrival:
        L += ["  arrivedAtDestination: ArrivedAtDestination with performer := seller, controller := seller;"]
    L += [
        f"  {p.delivery_var}: {p.delivery_event} with {p.delivery_place_attr} := {p.delivery_place_param}, delDueDate := Date.add(effDate, deliveryDays, days), performer := seller, controller := seller;",
    ]
    if p.has_string_sale:
        L += ["  procuredSoDelivered: ProcuredSoDelivered with performer := seller, controller := seller;"]
    if p.has_bol:
        L += ["  billOfLadingIssued: BillOfLadingIssued with performer := carrier, controller := carrier;"]
    if p.has_documents:
        L += ["  documentsProvided: DocumentsProvided with performer := seller, controller := seller;"]
    if p.has_onboard_bl:
        L += [
            "  onBoardBLAgreed: OnBoardBLAgreed with performer := buyer, controller := buyer;",
            "  blInstructionGiven: BLInstructionGiven with performer := buyer, controller := buyer;",
            "  onBoardBLIssued: OnBoardBLIssued with performer := carrier, controller := carrier;",
            "  onBoardBLForwarded: OnBoardBLForwarded with performer := seller, controller := seller;",
        ]
    L += [
        "  deliveryNoticeGiven: DeliveryNoticeGiven with performer := seller, controller := seller;",
        "  goodsTakenOver: GoodsTakenOver with performer := buyer, controller := buyer;",
    ]
    if p.assist_to_buyer:
        L += [
            "  assistanceToBuyerRequested: AssistanceToBuyerRequested with performer := buyer, controller := buyer;",
            "  assistanceToBuyerProvided: AssistanceToBuyerProvided with performer := seller, controller := seller;",
            "  assistanceToBuyerReimbursed: AssistanceToBuyerReimbursed with performer := buyer, controller := buyer;",
        ]
    if p.assist_to_seller:
        L += [
            "  assistanceToSellerRequested: AssistanceToSellerRequested with performer := seller, controller := seller;",
            "  assistanceToSellerProvided: AssistanceToSellerProvided with performer := buyer, controller := buyer;",
            "  assistanceToSellerReimbursed: AssistanceToSellerReimbursed with performer := seller, controller := seller;",
        ]
    if p.has_failure_costs:
        L += [
            "  goodsIdentified: GoodsIdentified with performer := seller, controller := seller;",
            "  additionalCostsPaid: AdditionalCostsPaid with performer := buyer, controller := buyer;",
        ]
    L += [
        "  paid: Paid with amount := price, currency := curr, from := buyer, to := seller, payDueDate := Date.add(effDate, paymentDays, days), performer := buyer, controller := buyer;",
    ]
    return L


def emit_preconditions(c: RuleConfig) -> list[str]:
    return ["Preconditions", "  goods.quantity > 0;"]


def emit_obligations(c: RuleConfig) -> list[str]:
    p = c.profile
    # In string-sale rules, delivery may occur as physical delivery OR as
    # procurement of goods already so delivered; orderings and triggers that
    # key on "delivery" must accept either event.
    delivered = (
        f"(Happens({p.delivery_var}) or Happens(procuredSoDelivered))"
        if p.has_string_sale else f"Happens({p.delivery_var})"
    )
    L = ["Obligations"]
    pack_before = (
        f"ShappensBefore(packagedAndMarked, {p.delivery_var})\n"
        f"              or ShappensBefore(packagedAndMarked, procuredSoDelivered)"
        if p.has_string_sale else f"ShappensBefore(packagedAndMarked, {p.delivery_var})"
    )
    L += [
        "  // A1: the seller provides the commercial invoice in conformity with the",
        "  // contract of sale (what counts as conform is the sale contract's standard).",
        "  oProvideInvoice: O(seller, buyer, true, Happens(invoiceProvided));",
        "  // A8: checking, packaging and marking precede delivery.",
        f"  oPackage: O(seller, buyer, true, {pack_before});",
    ]
    if p.has_export_clearance:
        before = (
            f"ShappensBefore(exportCleared, {p.delivery_var})\n"
            f"              or ShappensBefore(exportCleared, procuredSoDelivered)"
            if p.has_string_sale else f"ShappensBefore(exportCleared, {p.delivery_var})"
        )
        L += [
            f"  // A7: the seller clears the goods for export before {p.export_before_phrase}.",
            f"  oExportClearance: O(seller, buyer, true, {before});",
        ]
    if p.has_security_compliance:
        if p.term_type == "F":
            sec = (
                f"ShappensBefore(securityComplied, {p.delivery_var})\n"
                f"              or ShappensBefore(securityComplied, procuredSoDelivered)"
            )
            sec_comment = "  // A4 (2020): the seller complies with transport-security requirements up to delivery."
        else:
            sec = "Happens(securityComplied)"
            sec_comment = (
                "  // A4 (2020): the seller complies with transport-security requirements for"
                "\n  // the transport to the destination (beyond the origin delivery event, so"
                "\n  // not bounded by it)."
            )
        L += [sec_comment, f"  oSecurityCompliance: O(seller, buyer, true, {sec});"]
    if p.has_seller_carriage:
        L += [
            f"  // A4: the seller contracts carriage to the named {p.carriage_dest_word}, at its own cost, in time.",
            "  oContractCarriage: O(seller, buyer, true,",
            "              WhappensBefore(carriageContracted, carriageContracted.dueDate)",
            f"              and carriageContracted.{p.carriage_dest_attr} == {p.dest_param});",
        ]
    if p.has_import_clearance:
        before = (
            f"ShappensBefore(importCleared, {p.delivery_var})\n"
            f"              or ShappensBefore(importCleared, procuredSoDelivered)"
            if p.has_string_sale else f"ShappensBefore(importCleared, {p.delivery_var})"
        )
        L += [
            "  // A7 (DDP): the seller also clears the goods for import before delivery at destination.",
            f"  oImportClearance: O(seller, buyer, true, {before});",
        ]
    if p.has_insurance:
        before = (
            f"(ShappensBefore(insuranceObtained, {p.delivery_var})\n"
            f"              or ShappensBefore(insuranceObtained, procuredSoDelivered))"
            if p.has_string_sale else f"ShappensBefore(insuranceObtained, {p.delivery_var})"
        )
        # L2: the ICC minimum is now a CHECKED ordered-enum constraint, not
        # data. CIF's floor is ICC(C); CIP's is ICC(A) (Incoterms 2020).
        min_clause = "A" if "(A)" in p.insurance_cover_phrase else ("B" if "(B)" in p.insurance_cover_phrase else "C")
        L += [
            f"  // A5: the seller takes out cargo insurance of at least {p.insurance_cover_phrase}",
            "  // (an ordered-enum minimum, checked), covering at least 110% of the price,",
            "  // in the contract currency - all three checked on the insurance event.",
            f"  oInsure: O(seller, buyer, true, {before}",
            "              and insuranceObtained.insuredAmount >= 1.1 * price",
            "              and insuranceObtained.insuredCurrency == curr",
            f"              and insuranceObtained.coverLevel >= ICCClause({min_clause}));",
            "  // A5: the seller provides the buyer with the policy/certificate or other",
            "  // evidence of cover (the buyer may claim directly from the insurer).",
            "  oProvideInsuranceDoc: Happens(insuranceObtained) -> O(seller, buyer, true,",
            "              Happens(insuranceDocProvided));",
            "  // A5 (conditional): when required by the buyer - and subject to the buyer",
            "  // providing the necessary information - the seller obtains additional",
            "  // War/Strikes cover at the buyer's cost ('if procurable' not modelled).",
            "  oAdditionalCover: Happens(additionalCoverRequested) -> O(seller, buyer,",
            "              Happens(additionalCoverInfoGiven), Happens(additionalCoverObtained));",
            "  // B9: the buyer pays for the additional cover it required.",
            "  oPayAdditionalCover: Happens(additionalCoverObtained) -> O(buyer, seller, true,",
            "              Happens(additionalCoverPaid));",
        ]
    if p.has_nomination:
        L += [
            f"  // A2 delivery: once the buyer has nominated the {p.transport_noun}, the seller must place",
            f"  // the goods {p.deliver_place_phrase}, at the named {p.nomination_place_word}, before the deadline",
            "  // - or procure goods already so delivered (string sales).",
            f"  oDeliver: Happens({p.nomination_var}) -> O(seller, buyer, true,",
            f"              (WhappensBefore({p.delivery_var}, {p.delivery_var}.delDueDate)",
            f"              and {p.delivery_var}.{p.delivery_place_attr} == {p.nomination_var}.{p.nomination_place_attr})",
            f"              or WhappensBefore(procuredSoDelivered, {p.delivery_var}.delDueDate));",
        ]
    elif p.has_string_sale:  # C/D-term: unconditional delivery, procurement alternative
        L += [
            p.c_deliver_comment[0],
            p.c_deliver_comment[1],
            "  // Alternatively the seller procures goods already so delivered (string sales).",
            "  oDeliver: O(seller, buyer, true,",
            f"              (WhappensBefore({p.delivery_var}, {p.delivery_var}.delDueDate)",
            f"              and {p.delivery_var}.{p.delivery_place_attr} == {p.delivery_place_param})",
            f"              or WhappensBefore(procuredSoDelivered, {p.delivery_var}.delDueDate));",
        ]
    else:  # E-term (EXW): unconditional delivery at the seller's premises, no string sale
        L += [
            p.c_deliver_comment[0],
            p.c_deliver_comment[1],
            "  oDeliver: O(seller, buyer, true,",
            f"              WhappensBefore({p.delivery_var}, {p.delivery_var}.delDueDate)",
            f"              and {p.delivery_var}.{p.delivery_place_attr} == {p.delivery_place_param});",
        ]
    if p.has_arrival:
        L += [
            "  // DPU sequencing: arrival at the destination strictly precedes the unloaded",
            "  // delivery - the seller's unloading duty, unique to DPU among the 11 rules",
            "  // (procuring goods already so delivered discharges it: they arrive unloaded).",
            f"  oUnload: O(seller, buyer, true, ShappensBefore(arrivedAtDestination, {p.delivery_var})",
            "              or Happens(procuredSoDelivered));",
        ]
    if p.has_documents and p.has_bol:
        L += [
            "  // A6: after loading, the carrier issues the bill of lading and the seller",
            p.provide_docs_line2,
            "  // Content requirements: dated within the shipment period; if negotiable,",
            "  // a full set of originals (customarily three) must be tendered.",
            f"  oProvideDocuments: {delivered} -> O(seller, buyer, true,",
            "              Happens(billOfLadingIssued) and Happens(documentsProvided)",
            f"              and WhappensBefore(billOfLadingIssued, {p.delivery_var}.delDueDate)",
            "              and (billOfLadingIssued.negotiable == false or billOfLadingIssued.originalsCount >= 3));",
        ]
    elif p.has_documents:
        L += [
            p.proof_docs_comment[0],
            p.proof_docs_comment[1],
            f"  oProvideDocuments: {delivered} -> O(seller, buyer, true,",
            "              Happens(documentsProvided));",
        ]
    if p.has_nomination and p.third_party_failure:
        _, fvar = p.third_party_failure
        notify_trigger = f"({delivered[1:-1]} or Happens({fvar}))" if p.has_string_sale else f"(Happens({p.delivery_var}) or Happens({fvar}))"
        notify_comment = [
            "  // A10 (dual notice): the seller notifies the buyer that the goods have been",
            f"  // delivered - or that the nominated {p.transport_noun} failed to take them in time.",
        ]
    else:
        notify_trigger = delivered
        notify_comment = [
            "  // A10: the seller notifies the buyer that the goods have been delivered and",
            "  // gives any notice the buyer needs to receive the goods.",
        ]
    L += notify_comment + [
        f"  oNotifyDelivery: {notify_trigger} -> O(seller, buyer, true,",
        "              Happens(deliveryNoticeGiven));",
    ]
    if p.has_onboard_bl:
        L += [
            "  // B6 (optional, if agreed): the buyer instructs its carrier - at the buyer's",
            "  // cost and risk - to issue the seller an on-board bill of lading.",
            "  oInstructCarrierBL: Happens(onBoardBLAgreed) -> O(buyer, seller, true,",
            "              Happens(blInstructionGiven));",
            "  // A6 (optional): once the carrier has issued the on-board B/L, the seller",
            "  // tenders it to the buyer (typically through the banking chain). The carrier",
            "  // is not bound by the sale contract, so issuance is a third-party event.",
            "  oForwardOnBoardBL: Happens(onBoardBLIssued) -> O(seller, buyer, true,",
            "              Happens(onBoardBLForwarded));",
        ]
    if p.has_nomination:
        L += [
            f"  // B4/B10: the buyer nominates the {p.transport_noun} and gives sufficient notice in time.",
            f"  {p.nominate_obl}: O(buyer, seller, true, WhappensBefore({p.nomination_var}, {p.nomination_var}.dueDate));",
        ]
    if p.has_schedule_notice:
        L += [
            "  // B10 (conditional): once it is agreed that the buyer may determine the",
            "  // time and/or point of delivery, the buyer must give sufficient notice in",
            "  // time; its failure is a B3/B9(d) premature-transfer trigger.",
            "  oNotifySchedule: Happens(scheduleRightAgreed) -> O(buyer, seller, true,",
            "              WhappensBefore(scheduleNotified, scheduleNotified.dueDate));",
        ]
    if p.has_buyer_import_clearance:
        b7_comment = (
            "  // B7: the buyer clears the goods for import (licences, security clearance,\n"
            "  // duties) in time; its failure is this rule's B3(a) premature-transfer trigger."
            if "import_clearance_violated" in p.b3_triggers else
            "  // B7 ('where applicable'): the buyer carries out and pays for transit and\n"
            "  // import clearance formalities in time."
        )
        L += [
            b7_comment,
            "  oImportClearanceBuyer: O(buyer, seller, true, WhappensBefore(importClearedByBuyer, importClearedByBuyer.dueDate));",
        ]
    if p.has_buyer_full_clearance:
        L += [
            "  // B7 EXW ('where applicable'): the buyer carries out and pays for all",
            "  // export, transit and import clearance formalities.",
            "  oClearanceBuyer: O(buyer, seller, true, WhappensBefore(clearedByBuyer, clearedByBuyer.dueDate));",
        ]
    L += [
        f"  // B2: the buyer takes delivery of the goods once they are {p.take_phrase}.",
        f"  oTakeDelivery: {delivered} -> O(buyer, seller, true, Happens(goodsTakenOver));",
    ]
    if p.assist_to_buyer:
        L += ["  // At the buyer's request, risk and cost, the seller provides assistance with:"]
        L += [f"  //   - {t}" for t in p.assist_to_buyer]
        L += [
            "  // The assistance must be provided in time - within assistDays of the",
            "  // request (L4: the deadline is relative to the request event's occurrence),",
            "  // so a failure to assist is a violation the B3/B9(d) limb can trigger on.",
            "  oAssistBuyer: Happens(assistanceToBuyerRequested) -> O(seller, buyer, true,",
            "              WhappensBefore(assistanceToBuyerProvided,",
            "                             Date.add(assistanceToBuyerRequested, assistDays, days)));",
            "  // B9: the buyer reimburses all costs of assistance it requested,",
            "  // within reimburseDays of the assistance being provided (L4: the",
            "  // deadline is relative to the assistance event's occurrence).",
            "  oReimburseSellerAssist: Happens(assistanceToBuyerProvided) -> O(buyer, seller, true,",
            "              WhappensBefore(assistanceToBuyerReimbursed,",
            "                             Date.add(assistanceToBuyerProvided, reimburseDays, days)));",
        ]
    if p.assist_to_seller:
        L += ["  // At the seller's request, risk and cost, the buyer provides assistance with:"]
        L += [f"  //   - {t}" for t in p.assist_to_seller]
        L += [
            "  // The assistance must be provided in time - within assistDays of the",
            "  // request (L4). For DDP this is the buyer's B7 import-clearance assistance,",
            "  // whose violation is that rule's B3(a) premature-transfer trigger.",
            "  oAssistSeller: Happens(assistanceToSellerRequested) -> O(buyer, seller, true,",
            "              WhappensBefore(assistanceToSellerProvided,",
            "                             Date.add(assistanceToSellerRequested, assistDays, days)));",
            "  // A9: the seller reimburses all costs of assistance it requested,",
            "  // within reimburseDays of the assistance being provided (L4: the",
            "  // deadline is relative to the assistance event's occurrence).",
            "  oReimburseBuyerAssist: Happens(assistanceToSellerProvided) -> O(seller, buyer, true,",
            "              WhappensBefore(assistanceToSellerReimbursed,",
            "                             Date.add(assistanceToSellerProvided, reimburseDays, days)));",
        ]
    return L


def emit_surviving(c: RuleConfig) -> list[str]:
    p = c.profile
    evidence = p.pay_evidence or ("the bill of lading" if p.has_bol else "the usual proof of delivery")
    delivered = (
        f"(Happens({p.delivery_var}) or Happens(procuredSoDelivered))"
        if p.has_string_sale else f"Happens({p.delivery_var})"
    )
    L = [
        "Surviving Obligations",
        f"  // B1: the buyer must pay the price for goods delivered {p.point_phrase} and evidenced",
        f"  // by {evidence}; this survives termination of the contract.",
        f"  oPay: ({delivered} and Happens({p.pay_second_conjunct})) -> Obligation(buyer, seller, true,",
        "              WhappensBefore(paid, paid.payDueDate) and paid.amount == price);",
    ]
    if p.has_failure_costs:
        parts, why = [], []
        for t in p.b3_triggers:
            if t == "nomination_violated":
                parts.append(f"Happens(Violated(obligations.{p.nominate_obl}))")
                why.append(f"the buyer fails to nominate the {p.transport_noun} in time")
            elif t in ("vessel_failed", "carrier_failed"):
                _, var = p.third_party_failure
                parts.append(f"Happens({var})")
                why.append("its nominee fails to take the goods")
            elif t == "import_clearance_violated":
                parts.append("Happens(Violated(obligations.oImportClearanceBuyer))")
                why.append("the buyer fails its B7 import-clearance duty")
            elif t == "take_delivery_violated":
                parts.append("Happens(Violated(obligations.oTakeDelivery))")
                why.append("the buyer fails to take delivery of the goods at its disposal")
            elif t == "notice_violated":
                parts.append("Happens(Violated(obligations.oNotifySchedule))")
                why.append("the buyer fails to give the agreed B10 notice in time")
            elif t == "assist_seller_violated":
                parts.append("Happens(Violated(obligations.oAssistSeller))")
                why.append("the buyer fails to give the seller its B7 clearance "
                           "assistance in time (DDP)")
        trigger = parts[0] if len(parts) == 1 else "(" + " or ".join(parts) + ")"
        L += [
            f"  // B3/B9(d): if {' or '.join(why)},",
            "  // the buyer bears the resulting additional costs - the rules' premature",
            "  // risk/cost transfer, guarded by the ICC proviso that the goods have been",
            "  // clearly identified as the contract goods. A surviving obligation: like",
            "  // the payment above, it outlives termination caused by the very failure",
            "  // that triggered it.",
            f"  oFailureCosts: {trigger} ->",
            "              Obligation(buyer, seller, Happens(goodsIdentified), Happens(additionalCostsPaid));",
        ]
    return L


def emit_powers(c: RuleConfig) -> list[str]:
    p = c.profile
    L = ["Powers"]
    if p.has_nomination:
        if p.third_party_failure:
            _, fvar = p.third_party_failure
            suspend_trigger = f"(Happens(Violated(obligations.{p.nominate_obl})) or Happens({fvar}))"
            suspend_comment = (
                f"  // If the buyer fails to nominate the {p.transport_noun} in time - or its nominee"
                "\n  // fails to take the goods - the seller may suspend delivery."
            )
        else:
            suspend_trigger = f"Happens(Violated(obligations.{p.nominate_obl}))"
            suspend_comment = f"  // If the buyer fails to nominate the {p.transport_noun} in time, the seller may suspend delivery."
        L += [
            suspend_comment,
            f"  pSuspendDelivery: {suspend_trigger} ->",
            "              P(seller, buyer, true, Suspended(obligations.oDeliver)) with Controller seller;",
            "  // A late nomination during the suspension resumes the delivery obligation.",
            f"  pResumeDelivery: HappensWithin({p.nomination_var}, Suspension(obligations.oDeliver)) ->",
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
    if p.has_import_clearance:
        L += [
            "  // If the seller fails to clear the goods for import, the buyer may terminate.",
            "  pTerminateNoImportClearance: Happens(Violated(obligations.oImportClearance)) -> P(buyer, seller, true, Terminated(self));",
        ]
    if p.has_documents:
        L += [
            "  // B6: the buyer must accept conforming documents - so when the tendered",
            "  // documents are NOT in conformity with the contract, the buyer may suspend",
            "  // the (surviving) payment obligation until conforming documents arrive.",
            "  // Verified: powers may target surviving obligations (compiler + codegen).",
            "  pRejectDocuments: Happens(documentsProvided) ->",
            "              P(buyer, seller, documentsProvided.conforming == false, Suspended(obligations.oPay));",
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
    rules = [
        "read To buyer On goods.description by seller",
        "read To buyer On obligations.oDeliver by seller",
    ]
    if p.has_seller_carriage:
        rules.append("read To buyer On carriageContracted by seller")
    if p.has_insurance:
        rules.append("read To buyer On insuranceObtained by seller")
    if p.has_import_clearance:
        rules.append("read To buyer On importCleared by seller")
    if p.has_carrier:
        if not p.has_seller_carriage:  # F-term with a carrier (FOB): carrier reads delivery
            rules.append(f"read To carrier On {p.delivery_var} by seller")
        rules += [
            "read To seller On billOfLadingIssued by carrier",
            # The seller owns the B/L (the carrier issues it to the shipper), so
            # both billOfLading grants are the owner's: it authorizes the carrier
            # to inscribe the number at issuance, and...
            "write To carrier On billOfLading.blNumber by seller",
            # ...A6 document-of-title: the buyer receives TRANSFER rights over the
            # bill of lading - the AC ontology's transfer action standing in for
            # the negotiable document's endorsability (sale in transit), granted
            # by the holder as an endorsement is.
            "transfer To buyer On billOfLading by seller",
        ]
    else:  # proof-only rules: buyer reads the delivery event
        rules.append(f"read To buyer On {p.delivery_var} by seller")
    if p.has_onboard_bl:  # FCA optional B/L mechanism: carrier issues, seller forwards
        rules += [
            "read To seller On onBoardBLIssued by carrier",
            "read To buyer On onBoardBLForwarded by seller",
        ]
    rules.append("write To buyer On powers.pTerminateByBuyer by seller")

    L = ["ACPolicy with Controller seller"]
    L += [f"  Rule{i}: Grant {r};" for i, r in enumerate(rules, 1)]
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
