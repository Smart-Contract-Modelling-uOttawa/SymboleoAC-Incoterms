// Scenario-execution harness for the generated SymboleoAC JS.
//
// The compiler emits Hyperledger Fabric chaincode: a package per rule under
// generated/<CODE>/, whose norm logic lives in domain/contract/<CODE>.js +
// events.js on top of the `symboleoac-js-core` runtime. The Fabric wrapper
// (index.js -> fabric-shim) is irrelevant to the contract semantics, so we
// stub index.js in the require cache and drive the contract directly:
//
//   const rule = loadRule('generated', 'FOB');
//   const c = makeContract(rule, [ ...ctorArgs ]);          // activates + triggers norms
//   fire(rule, c, 'vesselNominated', { loadingPort: 'X' }); // an event Happens
//   violate(rule, c, 'oDeliver');                           // force a breach
//   c.obligations.oDeliver.isFulfilled();  c.isSuccessfulTermination();
//
// Both the harness and the generated code resolve `symboleoac-js-core` from
// tests/scenarios/node_modules, so they share the one runtime singleton
// (Events is stateful) — a prerequisite for the event bus to work.

import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(import.meta.url);

export function loadRule(genDir, code) {
  const pkgRoot = path.resolve(genDir, code);
  // Stub index.js (Fabric glue) so requiring the contract never loads fabric-shim.
  // FOB.js imports { contracts } from ../../index.js but never uses it.
  const indexPath = require.resolve(path.join(pkgRoot, 'index.js'));
  require.cache[indexPath] = {
    id: indexPath, filename: indexPath, loaded: true, exports: { contracts: {} },
  };
  const core = require('symboleoac-js-core');
  const { getEventMap, EventListeners } = require(path.join(pkgRoot, 'events.js'));
  const ContractClass = require(path.join(pkgRoot, 'domain', 'contract', `${code}.js`))[code];
  if (typeof ContractClass !== 'function') {
    throw new Error(`contract class ${code} not found in generated/${code}`);
  }
  return { code, core, getEventMap, EventListeners, ContractClass };
}

// Construct the contract, wire the event bus, activate, and trigger the
// unconditional norms — the same start-up index.js performs on init.
export function makeContract(rule, ctorArgs) {
  const contract = new rule.ContractClass(...ctorArgs);
  rule.core.Events.init(rule.getEventMap(contract), rule.EventListeners);
  if (!contract.activated()) {
    throw new Error(`${rule.code}: contract failed to activate (preconditions)`);
  }
  for (const obl of Object.values(contract.obligations)) {
    obl.trigerredUnconditional();
  }
  return contract;
}

// Rebuild the event map against the contract's *current* norms. The map
// captures object references (e.g. obligations.oDeliver) at build time, and
// several norms are created lazily by listeners, so the map must be rebuilt
// before each emit for subscriptions on those norms (e.g. obligation-Violated
// -> create-power) to match. This mirrors the per-transaction re-init the
// generated Fabric wrapper does when it reconstructs the contract from state.
function reinit(rule, contract) {
  rule.core.Events.init(rule.getEventMap(contract), rule.EventListeners);
}

// An event Happens: stamp it (with any attribute values) and emit it on the bus
// so the listeners re-evaluate and transition the norms.
export function fire(rule, contract, eventVar, attrs = {}) {
  const ev = contract[eventVar];
  if (ev == null) throw new Error(`${rule.code}: no event '${eventVar}'`);
  reinit(rule, contract);
  ev.happen(attrs);
  const { Events, InternalEvent, InternalEventSource, InternalEventType } = rule.core;
  Events.emitEvent(
    contract,
    new InternalEvent(InternalEventSource.contractEvent, InternalEventType.contractEvent.Happened, ev),
  );
  return contract;
}

// Force an obligation into Violation and emit the obligation-Violated event,
// standing in for the engine's deadline-expiry detection. This is how a breach
// path exercises the remedial powers (e.g. a terminate power becoming active).
export function violate(rule, contract, oblName) {
  const obl = contract.obligations[oblName];
  if (obl == null) throw new Error(`${rule.code}: no obligation '${oblName}'`);
  reinit(rule, contract);
  obl.violated();
  const { Events, InternalEvent, InternalEventSource, InternalEventType } = rule.core;
  Events.emitEvent(
    contract,
    new InternalEvent(InternalEventSource.obligation, InternalEventType.obligation.Violated, obl),
  );
  return contract;
}

// A future/past ISO date `days` from a base (default: now), for deadlines.
export function isoOffsetDays(days, base = new Date()) {
  const d = new Date(base.getTime() + days * 86400000);
  d.setSeconds(0, 0);
  return d.toISOString();
}
