# Governance Rules (Binding)

## Canonical references
- Architecture: `CSS-ARCH-DOC-001.md`
- Governance & canonical truth: `CSS-GOV-DOC-002.md`
- Constitution (core record): `constitution/CORE_CONSTITUTION.md`
- Triad roles (authoritative): `SOVEREIGN_MODEL_POLICY.md`

## Invariants
- No deployment without a promotion decision in `registry/promotions.yaml`
- No promotion without referenced eval artifacts
- No model or dataset without a unique ID, hash, owner, and card

## Roles
- Author: produces candidates
- Evaluator: owns eval integrity
- Approver: signs promotion
- Ops: operates pipelines

## Automation Rule
Automation may:
- train
- evaluate
- propose promotions

Automation may not:
- approve promotions
- deploy without approval
