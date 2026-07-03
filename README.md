# SymboleoAC-Incoterms

**Formalizing the Incoterms® 2020 trade terms as executable [SymboleoAC](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC2SC) contracts — with a coverage analysis and a validation strategy.**

Incoterms 2020 (ICC) defines **11 standard trade terms** (EXW, FCA, CPT, CIP, DAP, DPU, DDP, FAS, FOB, CFR, CIF) that allocate the *delivery point, risks, costs, insurance, clearance, documents, and notices* between seller and buyer. This project:

1. **Specifies each of the 11 rules in SymboleoAC** — a shared domain ontology plus one contract per term, generated consistently from the ICC allocation tables.
2. **Analyzes coverage** — an A1–A10 / B1–B10 × 11-rules traceability matrix recording what SymboleoAC can and cannot express, and why.
3. **Validates** the specs — static compilation, structural checks, and scenario-based execution of the generated JavaScript.

This backs a paper on the extent to which SymboleoAC supports a real, widely-used contractual standard.

## Status

| Rule | Spec | Compiles | Scenarios |
|------|------|:--------:|:---------:|
| FOB — Free on Board | [specs/FOB.symboleo](specs/FOB.symboleo) | ✅ | ⬜ |
| EXW, FCA, CPT, CIP, DAP, DPU, DDP, FAS, CFR, CIF | — | ⬜ | ⬜ |

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
