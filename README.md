# SymboleoAC-Incoterms

[![compile-specs](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-Incoterms/actions/workflows/ci.yml/badge.svg)](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-Incoterms/actions/workflows/ci.yml)

**Formalizing the Incoterms® 2020 trade terms as executable [SymboleoAC](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC2SC) contracts — with a coverage analysis and a validation strategy.**

Incoterms 2020 (ICC) defines **11 standard trade terms** (EXW, FCA, CPT, CIP, DAP, DPU, DDP, FAS, FOB, CFR, CIF) that allocate the *delivery point, risks, costs, insurance, clearance, documents, and notices* between seller and buyer. This project:

1. **Specifies each of the 11 rules in SymboleoAC** — a shared domain ontology plus one contract per term, generated consistently from the ICC allocation tables.
2. **Analyzes coverage** — an A1–A10 / B1–B10 × 11-rules traceability matrix recording what SymboleoAC can and cannot express, and why.
3. **Validates** the specs — static compilation, structural checks, and scenario-based execution of the generated JavaScript.

This backs a paper on the extent to which SymboleoAC supports a real, widely-used contractual standard.

## Status

**All 11 rules are specified and compile with 0 errors / 0 warnings.**

| Rule | Term type | Mode | Spec | Compiles | Scenarios |
|------|-----------|------|------|:--------:|:---------:|
| EXW — Ex Works | E (minimum) | any | [specs/EXW.symboleo](specs/EXW.symboleo) | ✅ | ⬜ |
| FCA — Free Carrier | F | any | [specs/FCA.symboleo](specs/FCA.symboleo) | ✅ | ⬜ |
| FAS — Free Alongside Ship | F | sea | [specs/FAS.symboleo](specs/FAS.symboleo) | ✅ | ⬜ |
| FOB — Free on Board | F | sea | [specs/FOB.symboleo](specs/FOB.symboleo) | ✅ | ⬜ |
| CPT — Carriage Paid To | C | any | [specs/CPT.symboleo](specs/CPT.symboleo) | ✅ | ⬜ |
| CFR — Cost and Freight | C | sea | [specs/CFR.symboleo](specs/CFR.symboleo) | ✅ | ⬜ |
| CIP — Carriage and Insurance Paid To | C + ins. | any | [specs/CIP.symboleo](specs/CIP.symboleo) | ✅ | ⬜ |
| CIF — Cost, Insurance and Freight | C + ins. | sea | [specs/CIF.symboleo](specs/CIF.symboleo) | ✅ | ⬜ |
| DAP — Delivered At Place | D | any | [specs/DAP.symboleo](specs/DAP.symboleo) | ✅ | ⬜ |
| DPU — Delivered at Place Unloaded | D | any | [specs/DPU.symboleo](specs/DPU.symboleo) | ✅ | ⬜ |
| DDP — Delivered Duty Paid | D (maximum) | any | [specs/DDP.symboleo](specs/DDP.symboleo) | ✅ | ⬜ |

Specs are generated (`python generator/generate.py`); CI enforces they never
drift from the generator. See [generator/README.md](generator/README.md).
Coverage per Incoterms article is in [coverage/coverage-matrix.md](coverage/coverage-matrix.md).
Scenario execution (next milestone) will fill the last column.

## Layout

```
specs/         the 11 SymboleoAC contracts + specs/common (shared ontology)
generator/     table-driven emitter: ICC allocation tables → .symboleo
coverage/      A1–A10 / B1–B10 × 11-rules support matrix
tests/         compile gate, structural checks, execution scenarios
paper/         the paper (source, figures, tables)
```

## Reading order

1. [STRATEGY.md](STRATEGY.md) — the plan: generation approach, coverage framework, validation layers.
2. [coverage/coverage-matrix.md](coverage/coverage-matrix.md) — what's covered / not.
3. [CLAUDE.md](CLAUDE.md) — how to compile a spec, the grammar, and reused tooling.

## Related

- **SymboleoAC language & compiler:** https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC2SC
- **Web IDE (edit, validate, generate, visualize specs in the browser):** https://smart-contract-modelling-uottawa.github.io/SymboleoAC-Web/
