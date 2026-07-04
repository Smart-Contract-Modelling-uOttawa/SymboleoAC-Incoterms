# Validation

Four layers (see ../STRATEGY.md §3). Start with the compile gate; add the rest
as specs land.

## 1. Static — compile gate (`tests/compile/`)

Every `specs/*.symboleo` must compile with **0 errors**. The gate runs the whole
`specs/` dir through the SymboleoAC codegen and fails on any `summary.errors != 0`.
It has **two interchangeable backends**, selected by env:

| Backend | Env | Used by | Why |
|---------|-----|---------|-----|
| Local jar | `CODEGEN_JAR` = path to the codegen-cli fat jar | local dev, reproducibility | offline, no live service |
| Remote bridge | `BACKEND_URL` = deployed SymboleoAC-Web bridge | CI | no jar/Maven in CI; same codegen the Web IDE uses |

Both return the same JSON (`{summary:{generatedFiles,warnings,errors}, issues}`) —
the remote `/generate` endpoint just shells out to that jar.

```bash
# portable gate (jar OR remote), loops every spec:
CODEGEN_JAR=/path/to/symboleoac-codegen-cli-1.0.0-all.jar  tests/compile/run.sh
BACKEND_URL=https://159-69-216-244.sslip.io                tests/compile/run.sh

# Windows local dev (jar only):
$env:CODEGEN_JAR = "C:\...\symboleoac-codegen-cli-1.0.0-all.jar"; .\tests\compile\run.ps1

# one spec, by hand:
cat specs/FOB.symboleo | java -jar "$CODEGEN_JAR"
# expect: {"summary":{"generatedFiles":N,"warnings":0,"errors":0}} and exit 0
```

Obtain `CODEGEN_JAR` by building from
https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC2SC, or reuse the
`codegen-cli` fat jar from SymboleoAC-Web (same upstream grammar).

CI (`.github/workflows/ci.yml`) runs `run.sh` in **remote** mode over every spec
on push. Override the endpoint with a `BACKEND_URL` repo variable.

## 2. Structural (`tests/`)

Run the compiler with `--model` and assert, per spec:
- it contains the norms its coverage-matrix row requires;
- every `obligations.x` / `powers.x` cross-reference resolves;
- role/asset/event references are all bound.

## 3. Scenario execution (`tests/scenarios/`) — implemented ✅

Drives event traces on the generated JS (`symboleoac-js-core`) and asserts the
resulting norm/contract states. **36 tests across all 11 rules.**

```bash
cd tests/scenarios && npm install
CODEGEN_JAR=/path/to/…-all.jar  npm run gen   # or: BACKEND_URL=https://…  npm run gen
npm test                                       # node --test
npm run coverage                               # c8 coverage of the generated norm logic
```

- **happy path** (11) — fire every obligation's events in order → all obligations
  (incl. the surviving `oPay`) reach `Fulfillment` and the contract reaches
  `SuccessfulTermination`.
- **breach** (25) — violate an obligation → the matching remedial power is created:
  a seller obligation → the buyer's terminate power (`oDeliver`→`pTerminateByBuyer`,
  `oInsure`→`pTerminateNoInsurance`, `oContractCarriage`→`pTerminateNoCarriage`,
  `oImportClearance`→`pTerminateNoImportClearance`); `oTakeDelivery` (all rules) →
  `pTerminateBySeller`; and, for the F-terms, `oNominate{Vessel,Carrier}` →
  `pSuspendDelivery`.

**Coverage.** The suite drives all 66 obligations to fulfillment and creates 35 of
38 powers (every remedial power type except the resume power, which needs a power's
*execution* rather than an obligation's violation). `npm run coverage` reports
≈90% line / ≈97% function coverage of the generated norm logic (`c8`).

How it works (see `harness.mjs`): the compiler emits Fabric chaincode, but the
norm logic is in `domain/contract/<CODE>.js` + `events.js` on `symboleoac-js-core`.
The harness stubs the Fabric wrapper (`index.js`) in the require cache and drives
the contract directly — construct, `Events.init`, then `fire(event)` /
`violate(obl)` — rebuilding the event map before each emit (mirroring the
per-transaction re-init the Fabric wrapper does), since some norms are created
lazily. `scenarios.mjs` holds the per-rule constructor args + event traces;
`generate.mjs` (re)builds `generated/` (gitignored).

> **Known upstream codegen bug (worked around):** the generated
> `createSurvivingObligation_*` listener references an undeclared `isNewInstance`
> (`!isNewInstance &&true`), throwing `ReferenceError` when any surviving `oPay`
> is created. `generate.mjs` rewrites it to `true` on the way out (see
> `patchCodegen`). Fix belongs in SymboleoAC2SC; remove the patch once landed.

## 4. Differential

Encode inter-rule expectations from `generator/incoterms.data.yaml` as
assertions, e.g.:
- CIF/CIP have a seller `insure` obligation; FOB/FAS/FCA do not;
- risk passes strictly later under CFR than FOB on the same trace;
- D-rules place the delivery point at destination, not origin.

These catch generator drift when a template changes.
