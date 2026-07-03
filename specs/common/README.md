# Shared domain ontology

The single vocabulary all 11 specs draw from, so contracts differ only in their
**norms and delivery point**, not in incidental naming. Factor this out of
`../FOB.symboleo` as the first generation step.

Planned shared elements (extend as rules are added):

- **Roles:** `Seller`, `Buyer`, `Carrier` (thirdParty), and — where a rule needs
  them — `Insurer`, `CustomsAuthority` (thirdParty).
- **Assets:** `Goods` (description, quantity, owner), `BillOfLading` /
  `TransportDocument` (number, owner), optionally `InsurancePolicy`.
- **Events (parametric):** vessel/carrier nomination, export clearance, carriage,
  loading / delivery-at-point, insurance taken out, document issuance, document
  hand-over, take-over, import clearance, payment.
- **Enumerations:** `Currency`, and any cover-level enum for insurance.

Note: SymboleoAC has no include/import mechanism, so "shared" means the generator
inlines these into each emitted spec (identical text across specs), not a literal
shared file the specs reference.
