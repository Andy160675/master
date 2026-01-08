# **Risk Taxonomy v0.1 — Deterministic Binding Specification**

**Status:** Defined / Not Active
**Consumes:** Fact Context (`facts_version` pinned)
**Produces:** `risk_level` (single enum)
**Used by:** Autonomy Resolver v0.1, Governor v0.4
**Design principle:** *Risk is derived, not judged.*

---

## 1. Purpose (Narrow and Mechanical)

The Risk Taxonomy answers **one question only**:

> *Given an asserted fact context, what is the canonical risk level?*

It does **not** recommend actions, assess intent, or weigh narratives.

---

## 2. Canonical `risk_level` Enum (Closed Set)

```text
LOW < MEDIUM < HIGH < CRITICAL
```

Ordering is absolute and globally enforced.

---

## 3. Inputs (Read-Only)

The taxonomy consumes **only normalized facts**, never raw evidence.

```json
{
  "facts_version": "0.1",
  "subject.type": "individual | organisation",
  "mission_class": "A1 | A2 | A3",

  "safety.*": "...",
  "integrity.*": "...",
  "platform.*": "...",

  "audit.audit_trace_complete": true | false,
  "sources.count": integer
}
```

> Any missing required fact → **fail closed** (see Rule 9).

---

## 4. Risk Derivation Rules (Strict Priority Order)

First matching rule sets `risk_level`. No averaging. No blending.

---

### **Rule 1 — Audit Integrity Failure**

```text
IF audit.audit_trace_complete == false
→ CRITICAL
```

Reason: unverifiable state is maximal risk.

---

### **Rule 2 — Safety Criticals**

```text
IF safety.contains_minor == true
OR safety.self_harm_promotional == true
OR safety.adult_content == true
→ CRITICAL
```

---

### **Rule 3 — Organisational Conduct Exposure**

```text
IF subject.type == organisation
AND integrity.misconduct_evidentiary == true
→ HIGH
```

This captures **recorded conduct**, not allegations.

---

### **Rule 4 — Mission Class Ceiling**

```text
IF mission_class == A3
→ CRITICAL

IF mission_class == A2
→ HIGH
```

Mission class is authoritative and pre-assigned.

---

### **Rule 5 — Integrity Breach (Non-Safety)**

```text
IF integrity.misleading_claim == true
OR integrity.deceptive_wording == true
→ HIGH
```

---

### **Rule 6 — Platform / Legal Sensitivity**

```text
IF platform.region in ["UK", "EU"]
AND integrity.public_interest_claim == true
→ HIGH
```

Jurisdiction raises exposure but not to CRITICAL alone.

---

### **Rule 7 — Weak Corroboration**

```text
IF sources.count < 3
→ MEDIUM
```

---

### **Rule 8 — Clean, Bounded Case**

```text
IF all safety.* == false
AND all integrity.* == false
AND mission_class == A1
→ LOW
```

---

### **Rule 9 — Fail-Closed Default**

```text
ELSE
→ HIGH
```

> **Important:**
> Unknown ≠ LOW.
> Unknown = elevated exposure.

---

## 5. Output Contract (Deterministic)

```json
{
  "risk_level": "HIGH",
  "risk_taxonomy_version": "0.1",
  "triggered_rule": "RULE_3_ORG_CONDUCT",
  "inputs_hash": "sha256(...)"
}
```

### Notes:

* `triggered_rule` is a **code**, not prose.
* `inputs_hash` binds the decision to exact facts.

---

## 6. Audit Requirements

Each derivation emits a single audit event:

```text
actor = risk_taxonomy
event_type = risk_derivation
risk_level = <enum>
rule_id = <triggered_rule>
facts_version = <pinned>
taxonomy_version = 0.1
```

This guarantees replayability.

---

## 7. Explicit Non-Capabilities

The Risk Taxonomy **cannot**:

* Lower risk based on human confidence
* Consider intent, remorse, or explanation
* Override facts
* Override mission class
* Consult policy or autonomy logic

It is upstream and blind by design.

---

## 8. Binding Effect on Autonomy Resolver

With this spec in place:

* **Rule 2 (Org High-Risk)** in Autonomy Resolver is now deterministic
* **Rule 6 (Low-Risk Auto-Execute)** is no longer discretionary
* **Rule 7 (Fail-Closed)** is enforced *before* routing, not during

Autonomy becomes **structurally constrained**, not procedurally polite.

---

## 9. State Declaration (Updated)

* **Risk Taxonomy v0.1:** ✅ **Defined / Not Active**
* **Governor v0.4:** ✅ **SEALED (enforced)**
* **Autonomy Resolver v0.1:** ✅ Defined / Not Active
* **Organisation Response Protocol v0.1:** ⏳ Next artifact

---

### Result

You now have a **three-layer deterministic chain**:

```text
FACTS → RISK (Taxonomy) → ROUTING (Autonomy Resolver)
```

No human intuition can leak into the middle.

---

### Next Clean Move (When You Say So)

Formalize **Organisation Response Protocol v0.1** as:

> *The only lawful action space available to organisations once risk ≥ HIGH.*

That will complete the asymmetry loop **without touching autonomy or policy again**.
