// Build step for the scenario tests: generate the JavaScript for every spec
// into ./generated/<CODE>/, so the tests can require and drive it.
//
// Source of the generated JS (same options as the compile gate, tests/compile):
//   CODEGEN_JAR  local codegen-cli fat jar (preferred for local dev), or
//   BACKEND_URL  the deployed SymboleoAC-Web bridge (used by CI).
//
// A known upstream codegen defect is patched on the way out (see patchCodegen).
// The generated/ tree is disposable (gitignored) — regenerate with `npm run gen`.

import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const specsDir = path.resolve(here, '..', '..', 'specs');
const outDir = path.join(here, 'generated');

export const ALL_CODES = ['EXW', 'FCA', 'FAS', 'FOB', 'CPT', 'CFR', 'CIP', 'CIF', 'DAP', 'DPU', 'DDP'];

// KNOWN UPSTREAM CODEGEN BUG (SymboleoAC2SC): the generated
// createSurvivingObligation_<x> listener references an undeclared
// `isNewInstance` (the regular createObligation_<x> listeners declare it), so
// the guard `!isNewInstance &&true` throws `ReferenceError: isNewInstance is
// not defined` the moment a surviving obligation (every spec's oPay) is created.
// We rewrite it to `true`, which is the intended behaviour for a freshly
// created surviving obligation. Remove this once the generator is fixed.
export function patchCodegen(js) {
  // Exact shape emitted for antecedent-`true` surviving obligations (oPay).
  js = js.split('!isNewInstance &&true').join('true');
  // General shape: any other use of the undeclared identifier inside a
  // createSurvivingObligation_* body (e.g. oFailureCosts, whose antecedent is
  // the goods-identified proviso) — declare it at the top of the function.
  // The legitimate inner `const isNewInstance = ...` shadows this harmlessly.
  js = js.replace(
    /createSurvivingObligation_(\w+)\(contract\) \{\n/g,
    (m, name) =>
      `createSurvivingObligation_${name}(contract) {\n` +
      `    const isNewInstance = contract.survivingObligations.${name} != null && contract.survivingObligations.${name}.isFinished();\n`,
  );
  // SECOND UPSTREAM CODEGEN BUG: an arithmetic expression in a consequent
  // (e.g. `insuredAmount >= 1.1 * price`) is compiled correctly in the norm
  // evaluation (events.js) but the LegalSituation metadata builder in the
  // contract class nests a stringified addConsequentOf(...) inside the
  // rightSide string with unescaped quotes - a JS SyntaxError ("Unexpected
  // number"). Rewrite the nested garbage into the intended flat expression.
  js = js.replace(
    /rightSide: 'this\.\w+Situation\.addConsequentOf\(\{ leftSide:'([\d.]+)', op:'([*+/-])',\s*rightSide: '([\w.]+)', _type: 'Condition'\}\)\s*\n\s*', _type: 'Condition'\}\)/g,
    "rightSide: '$1 $2 $3', _type: 'Condition'})",
  );
  return js;
}

async function generateFiles(source) {
  if (process.env.CODEGEN_JAR) {
    const out = execFileSync('java', ['-jar', process.env.CODEGEN_JAR], {
      input: source, maxBuffer: 1 << 27,
    });
    return JSON.parse(out.toString('utf8'));
  }
  if (process.env.BACKEND_URL) {
    const res = await fetch(`${process.env.BACKEND_URL}/generate`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ source }),
    });
    if (!res.ok) throw new Error(`backend ${res.status}: ${await res.text()}`);
    return res.json();
  }
  throw new Error('set CODEGEN_JAR (local jar) or BACKEND_URL (remote bridge)');
}

export async function generate(codes = ALL_CODES) {
  for (const code of codes) {
    const src = readFileSync(path.join(specsDir, `${code}.symboleo`), 'utf8');
    const { summary, files } = await generateFiles(src);
    if (!summary || summary.errors !== 0) {
      throw new Error(`${code}: expected 0 errors, got ${JSON.stringify(summary)}`);
    }
    rmSync(path.join(outDir, code), { recursive: true, force: true });
    for (const [rel, content] of Object.entries(files)) {
      const full = path.join(outDir, rel);
      mkdirSync(path.dirname(full), { recursive: true });
      writeFileSync(full, rel.endsWith('.js') ? patchCodegen(content) : content);
    }
    console.log(`gen ${code}: ${Object.keys(files).length} files`);
  }
}

// Ensure generated/<CODE> exists; generate on demand (tests call this).
export async function ensureGenerated(codes = ALL_CODES) {
  const missing = codes.filter((c) => !existsSync(path.join(outDir, c, 'events.js')));
  if (missing.length) await generate(missing);
  return outDir;
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1] === fileURLToPath(import.meta.url)) {
  const codes = process.argv.slice(2).length ? process.argv.slice(2) : ALL_CODES;
  generate(codes).catch((e) => { console.error(e.message); process.exit(1); });
}
