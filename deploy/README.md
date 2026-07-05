# Deploying a generated Incoterms contract to Hyperledger Fabric

This guide documents how to take one of the generated `specs/*.symboleo` rules,
compile it to a SymboleoAC chaincode, and **deploy and run it on Hyperledger
Fabric**, end to end. It was written from an actual, working deployment of
`FOB` and records every fix required along the way — including several that are
not obvious from the upstream READMEs.

It uses three upstream repositories from the uOttawa Smart-Contract-Modelling group:

| Repo | Role here |
|------|-----------|
| [SymboleoAC-HyperledgerFabric-Test-Netwrok](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-HyperledgerFabric-Test-Netwrok) | the Fabric test network (`network.sh`, bundled Fabric 2.2 binaries, sample chaincodes) |
| [SymboleoAC-JS-Core](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-JS-Core) | the `symboleoac-js-core` runtime the generated chaincode depends on |
| [SymboleoAC-Application-API](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-Application-API) | the client that enrolls role identities and invokes transactions |

> **TL;DR of the non-obvious fixes** (details below): the test-network `network.sh`
> is hard-wired to macOS binaries; the chaincode build needs `strict-ssl=false`
> behind a TLS-intercepting proxy; the Fabric 2.2 Node chaincode runtime is
> **Node 12**, which crashes on modern dependency syntax; and the SymboleoAC
> access-control layer requires each **role to carry a `dept` attribute** and
> each caller identity to carry `HF.name` / `HF.role` / `organization` /
> `department` attributes.

## 0. Prerequisites

- **Docker Desktop** with the WSL2 backend (Windows) or Docker Engine (Linux/mac).
- **A Linux host.** The network is bash + Linux Fabric binaries. On Windows use
  **WSL2 Ubuntu** (`wsl --install Ubuntu`) with Docker Desktop's *Settings →
  Resources → WSL integration* enabled for that distro. Verify with
  `wsl -d Ubuntu -u root -- docker version`.
- `git`, `jq`, `curl` inside the Linux host (`apt-get install -y git jq curl`).
- Java 17+ and this repo's codegen jar / bridge, only if you regenerate the
  chaincode JS (see step 3).

### 0.1 If Docker Desktop won't start (stale-socket bug)

We hit a Docker Desktop startup failure where the engine never came up and the
log showed, e.g.:

```
starting services: initializing Inference manager: listening on
unix://…\Docker\run\dockerInference: remove …\dockerInference:
The file cannot be accessed by the system.
```

Cause: optional services (the **Model Runner / "Inference manager"** and the
**Secrets Engine**) try to bind AF_UNIX sockets under `%LOCALAPPDATA%`, first
removing a stale socket left by a prior unclean shutdown — and Windows cannot
delete those phantom socket files, so the whole backend aborts. Fix:

1. Quit Docker Desktop (leave `com.docker.service` running).
2. **Move the offending socket directories aside** so Docker recreates clean ones
   (they cannot be deleted, but the *directory* can be renamed):
   `%LOCALAPPDATA%\Docker\run` and `%LOCALAPPDATA%\docker-secrets-engine`.
   Do this for *all* offending dirs in one pass — each crash re-stales them.
3. Permanently disable the Model Runner: `docker desktop disable model-runner`.
4. Relaunch Docker Desktop; `docker ps` should now succeed.

(A reboot also clears the phantom socket handles.)

## 1. The Fabric test network

```bash
git clone https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-HyperledgerFabric-Test-Netwrok.git net
cd net
chmod +x network.sh; find bin -maxdepth 1 -type f -exec chmod +x {} +; find scripts -name '*.sh' -exec chmod +x {} +
```

**Fix 1 — `network.sh` points at macOS binaries.** Line ~15 reads
`export PATH=${PWD}/bin-macos:$PATH`. The repo ships both `bin/` (Linux) and
`bin-macos/` (macOS); on Linux this picks Mach-O binaries and every command fails
with *"Peer binary and configuration files not found.."*. Repoint it:

```bash
sed -i 's/bin-macos/bin/g' network.sh
```

Bring the network up (pulls Fabric 2.2.4 + CA 1.4.4 images the first time):

```bash
export PATH=$PWD/bin:$PATH
export FABRIC_CFG_PATH=$PWD/configtx
./network.sh up -ca -cai 1.4.4 -i 2.2.4
./network.sh createChannel -c mychannel
```

You should end up with `orderer.example.com`, `peer0.org1.example.com`,
`ca_org1`, `ca_orderer`, and `cli` containers running.

## 2. Prepare the chaincode

The generated JavaScript layout (`domain/`, `events.js`, `index.js`,
`serializer.js`, `package.json`) is exactly a Fabric Node chaincode directory.
Produce a patched package for a rule with this repo's scenario generator, which
already applies the required codegen fix, and copy it in as `<CODE>/`:

```bash
# in this (SymboleoAC-Incoterms) repo:
cd tests/scenarios
CODEGEN_JAR=/path/to/symboleoac-codegen-cli-*-all.jar node generate.mjs FOB   # or BACKEND_URL=…
cp -r generated/FOB /path/to/net/FOB
```

**Fix 2 — the `isNewInstance` codegen bug.** The generated
`createSurvivingObligation_*` listener references an undeclared `isNewInstance`,
crashing the chaincode at runtime the moment the surviving `oPay` obligation is
created. `generate.mjs` rewrites it to `true` (`patchCodegen`); confirm with
`grep -c 'isNewInstance &&true' FOB/events.js` → `0`. (Upstream fix belongs in
SymboleoAC2SC.)

## 3. Deploy

**Fix 3 — corporate TLS interception breaks the build's `npm install`.** The
Fabric Node builder runs `npm install` for the chaincode; behind a
TLS-intercepting proxy it fails with `UNABLE_TO_VERIFY_LEAF_SIGNATURE`. Add an
`.npmrc` to the chaincode source so the build skips cert verification:

```bash
printf 'strict-ssl=false\n' > /path/to/net/FOB/.npmrc
```

**Fix 4 — the Fabric 2.2 Node chaincode runtime is Node 12.** `hyperledger/fabric-nodeenv:2.2`
ships Node **v12.16.1**, which cannot parse `||=` used by a modern transitive
dependency (`@so-ric/colorspace`, pulled via `fabric-shim` → `winston`). The
chaincode container then exits with `SyntaxError: Unexpected token '='` during
registration. Give the peer a modern Node runtime by retagging a newer nodeenv
(Node 22) under the tag the 2.2 peer uses:

```bash
docker pull hyperledger/fabric-nodeenv:2.5           # Node 22
docker tag  hyperledger/fabric-nodeenv:2.5 hyperledger/fabric-nodeenv:2.2
```

Now deploy:

```bash
cd /path/to/net
export PATH=$PWD/bin:$PATH FABRIC_CFG_PATH=$PWD/config
./network.sh deployCC -c mychannel -ccn fob -ccv 1.0 -ccs 1 -ccp FOB -ccl javascript
```

Expected: `Chaincode definition committed on channel 'mychannel'`. The chaincode
container then starts on Node 22 and logs `ACPolicy loaded`.

## 4. Invoke — and the access-control requirement

The chaincode transaction interface (`index.js`): `init`; one `trigger_<event>`
per domain event; `p_<power>_…` power-execution methods; `violateObligation_<o>`;
and queries such as `getState` and `getLegalPositionStateAndTime`. `init` takes a
single JSON string of the contract parameters and **returns an auto-generated
`contractId`** (`FOB_<timestamp>`); every subsequent call passes
`{"contractId": …, "event": {…}}`.

A happy-path trace is: `init` → `trigger_vesselNominated` → `trigger_exportCleared`
→ `trigger_loadedOnBoard` → `trigger_billOfLadingIssued` →
`trigger_documentsProvided` → `trigger_goodsTakenOver` → `trigger_paid`, then query
the norm states (expect the obligations at *Fulfillment* and the contract at
*SuccessfulTermination*, mirroring `tests/scenarios/`).

**But every transaction is access-controlled.** `init` runs
`authenticate(HF.role, HF.name, organization, department)`, which matches the
caller's certificate attributes against a contract **role**
(`findObject(name, type)` then `org` and `dept` equality). Invoking with the
plain Org1 *Admin* identity returns:

```json
{"successful": false, "message": "Unauthorized: Unknown access"}
```

That is the **SymboleoAC access-control policy enforcing itself on-chain** — the
expected, correct behaviour, not a failure. To drive authorized transactions you
must invoke with an identity that carries the role attributes, as the
Application-API does:

- **Roles must declare `dept`.** `authenticate` compares
  `department === objRole.dept._value`, so each role needs a `dept: String`
  attribute. All of the group's example contracts include it; the Incoterms
  generator in this repo now emits it too (`Seller isA Role with name: String,
  org: String, dept: String;`). See the compiler issue linked below — the
  SymboleoAC2SC generator should add this automatically.
- **Enroll role identities with the CA** carrying, as `ecert` attributes,
  `HF.name` = the role variable (e.g. `seller`), `HF.role` = the role type
  (e.g. `Seller`), `organization` = the role's `org`, and `department` = the
  role's `dept`. The [Application-API](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-Application-API)
  (`CAUtil.js`, `app.js`) automates this via `fabric-ca-client`/the Node SDK; it
  is the supported client for building the per-event payloads and invoking as the
  right party. (Note it currently hard-codes a `fabric-network-2.2.2` layout and
  macOS paths that must be pointed at your network.)

## Toolchain issues encountered (summary)

| # | Symptom | Root cause | Fix |
|---|---------|-----------|-----|
| 0 | Docker engine won't start | phantom AF_UNIX sockets + Model Runner | rename `run`/`docker-secrets-engine` dirs; `docker desktop disable model-runner` |
| 1 | `Peer binary … not found` | `network.sh` uses `bin-macos` | `sed -i 's/bin-macos/bin/g' network.sh` |
| 2 | chaincode crashes at `oPay` | `isNewInstance` codegen bug | patched by `tests/scenarios/generate.mjs` |
| 3 | `npm install` `UNABLE_TO_VERIFY_LEAF_SIGNATURE` | TLS-intercepting proxy | `.npmrc` `strict-ssl=false` in the chaincode |
| 4 | container exits with `SyntaxError: '='` | `fabric-nodeenv:2.2` is Node 12 | retag `fabric-nodeenv:2.5` (Node 22) as `2.2` |
| 5 | `Unauthorized: Unknown access` | roles lack `dept`; caller lacks role attrs | add `dept` to roles; enroll role identities (Application-API) |
