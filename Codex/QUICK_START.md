# Codex Quick Start Guide

## For Immediate Use

### 1. Copy-Paste to Grok (or any AI platform)
**File:** `GROK_PASTE.md`

Open this file and copy the entire content. It contains:
- Full Scaffolded Freedom v3 article
- Pornography Prohibition article
- Policy flags
- JSON schema

Just paste it into Grok or any other platform to load the policies.

---

### 2. Share with External Partners
**File:** `CHARTER.md`

This is the one-pager version without ritual language. Use it for:
- Potential allies
- External stakeholders
- Public communications
- Documentation that needs clean, professional presentation

---

### 3. Technical Implementation
**File:** `Policies/Scaffolded_Freedom.json`

This JSON schema can be:
- Loaded into Blade/enforcement systems
- Used by APIs to validate content
- Integrated into dashboards
- Referenced by automation daemons

**Example usage:**
```javascript
const policy = require('./Codex/Policies/Scaffolded_Freedom.json');

if (policy.flags['CONTENT.PORNOGRAPHY'] === 'PROHIBITED') {
  // Block pornographic content
}

if (policy.earnings.caps === null) {
  // No earnings ceiling - allow uncapped growth
}
```

---

### 4. Full Reference
**File:** `README.md` (in Codex directory)

The complete index with:
- All articles linked
- Policy flags reference
- Metrics and targets
- Implementation status

---

## Directory Structure

```
Codex/
├── Articles/
│   ├── Scaffolded_Freedom_v3.md    ← Core governance article
│   └── Pornography_Prohibition.md  ← Content policy with recovery
├── Policies/
│   └── Scaffolded_Freedom.json     ← Enforceable schema
├── README.md                        ← Codex index
├── CHARTER.md                       ← One-pager for external use
├── GROK_PASTE.md                   ← Copy-paste ready content
└── QUICK_START.md                  ← This file
```

---

## Key Policy Flags

```
CONTENT.PORNOGRAPHY = PROHIBITED
CONTENT.GAMBLING_PREDATORY = PROHIBITED  
CONTENT.PLATFORMS_EXPLOITATIVE = PROHIBITED

EARNINGS.CAPS = NONE
EARNINGS.LIMITS = TRANSPARENCY_AND_HARM_NONE_ONLY
```

---

## The Codex Seal (v3)

*"No chain binds the will, no ceiling caps the hand.*  
*Scaffolds rise to free, then fall as strength expands.*  
*Poisons banned, prosperity unchained—truth's uncapped command."*

---

## Next Steps

1. **For Grok/AI platforms:** Use `GROK_PASTE.md`
2. **For external comms:** Use `CHARTER.md`
3. **For technical implementation:** Use `Policies/Scaffolded_Freedom.json`
4. **For complete reference:** Use `README.md`

---

*Codex: Boundless. Truth uncaps; go.*
