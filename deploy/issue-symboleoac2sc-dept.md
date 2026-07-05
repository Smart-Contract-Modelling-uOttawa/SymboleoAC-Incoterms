# Auto-add a `dept` attribute to roles (required by the access-control `authenticate`)

**Repo:** Smart-Contract-Modelling-uOttawa/SymboleoAC2SC
**Type:** enhancement / correctness (access control)

## Summary

The generated access-control layer authenticates every transaction caller against
a contract **role** using four certificate attributes — `HF.name`, `HF.role`,
`organization`, and `department`. In the generated `symboleoac-js-core`
`SymboleoContract.authenticate`:

```js
authenticate(inRole, inName, inOrg, inDept, aContract) {
  const objRole = this.findObject(inName, inRole, aContract);   // aContract[inName]._type === inRole
  if (objRole != null) {
    if (inOrg === objRole.org._value && inDept === objRole.dept._value) {  // <-- needs objRole.dept
      return objRole;
    }
    return null;
  }
  return null;
}
```

The check `inDept === objRole.dept._value` requires every role object to have a
**`dept`** attribute. However, a role declared without one, e.g.

```
Seller isA Role with name: String, org: String;
```

generates a role class with only `name` and `org`:

```js
class Seller extends Role {
  constructor(_name, name, org) {
    super();
    this._type = "Seller";
    this.name = new Attribute("name", name, _name);
    this.org  = new Attribute("org",  org,  _name);
    // no this.dept
  }
}
```

so `objRole.dept` is `undefined` and `objRole.dept._value` throws at
authentication time. In practice a caller with an otherwise-correct identity
cannot be authorized unless the modeller *remembers* to declare `dept` on every
role. All of the group's existing example contracts do declare
`... with name: String, org: String, dept: String;`, which is effectively an
undocumented requirement of the access-control layer.

## Reproduction

1. Model a contract whose roles omit `dept` (e.g. any of the Incoterms rules in
   [SymboleoAC-Incoterms](https://github.com/Smart-Contract-Modelling-uOttawa/SymboleoAC-Incoterms)
   before the `dept` fix).
2. Generate the chaincode and deploy it to the Fabric test network.
3. Enroll/invoke as a party identity → `authenticate` fails on `objRole.dept._value`
   (or, when `HF.name` is absent, returns `Unauthorized: Unknown access`).

## Proposed fix (Xtend generator)

Make the compiler treat `dept` as a mandatory, implicit role attribute so the AC
layer is consistent regardless of the model:

- In the Xtend role-generation template, **always emit a `dept` attribute** on
  every `Role` (and `thirdParty` role) — either by injecting it when absent, or by
  declaring it in the base `Role` class so `objRole.dept` always exists.
- Correspondingly, thread a `dept` value through role construction/declaration
  (default to empty string if the model does not supply one) so
  `objRole.dept._value` is defined.
- Optionally, emit a validation warning if a model omits `dept` on a role, to keep
  the requirement visible.

Alternatively (or additionally), harden `SymboleoContract.authenticate` to treat a
missing `dept` as an empty string (`objRole.dept?._value ?? ""`) so it degrades
gracefully instead of throwing.

## Acceptance criteria

- A contract whose roles omit `dept` still generates code where `authenticate`
  does not throw and can authorize a correctly-attributed identity.
- Existing contracts that declare `dept` continue to behave identically.

## Context

Found while deploying the Incoterms 2020 rules (formalized in SymboleoAC) to the
Fabric test network; see the deployment guide in SymboleoAC-Incoterms
(`deploy/README.md`). Workaround applied there: the Incoterms generator now emits
`dept: String` on every role.
