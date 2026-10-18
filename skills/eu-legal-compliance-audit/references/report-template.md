# Report template

Write the report in the user's language. Keep headings; drop sections that are empty. Translate labels (e.g. FAIL → INCUMPLE, PARTIAL → PARCIAL, PASS → CUMPLE, MANUAL → VERIFICAR) when the report is not in English.

```markdown
# Legal compliance audit — <project name>

**Date:** <YYYY-MM-DD> · **Scope:** <repo path / URL> · **Jurisdiction:** <country> (+ EU law)
**Profile assumed:** <B2C/B2B>, <size class>, <sells online yes/no>, <UGC yes/no>, <AI yes/no>
<If any profile item was assumed rather than confirmed, say which.>

> Technical pre-audit, not legal advice. Findings marked high exposure deserve review by a lawyer or DPO.

## Summary

| Status | Count |
|---|---|
| ❌ Fail | n |
| ⚠️ Partial | n |
| ✅ Pass | n |
| 🔍 Verify manually | n |

**Estimated sanction exposure (<country>, <currency>)**

| Scenario | Amount |
|---|---|
| Minimum (warnings where allowed, quick correction) | € … |
| **Expected (typical fines for an organisation of this size)** | **€ …** |
| Legal maximum (theoretical worst case) | € … |

Top 3 risks: 1) … 2) … 3) …

## Findings

Ordered by risk (likelihood of complaint × expected fine).

### ❌ F1 — <short title in plain language>
- **Controls:** CK-02, CK-03
- **Law:** <article(s)>
- **Evidence:** `src/layouts/Default.vue:14` loads `gtag.js` unconditionally; no consent check before `gtag('config')`. <Verified live: yes/no>
- **Why it matters:** <one or two sentences, user-facing>
- **Fix:** <concrete, developer-level steps>
- **Infraction / class:** LSSI 22.2 — leve
- **Exposure:** min € … · expected € … · max € …

### ⚠️ F2 — …

## Third-party services detected

| Service | Purpose | Vendor country | Receives personal data | Disclosed in privacy policy | Needs consent |
|---|---|---|---|---|---|

## Passed checks
One line per area, e.g. "Legal notice: complete (LEG-01)".

## Not applicable
One line, e.g. "No UGC → DSA not applicable; B2B only → consumer rules not applicable".

## Verify manually
- [ ] Data processing agreements with: <processors detected>
- [ ] Records of processing (Art. 30)
- [ ] …

## Cost estimate — method and breakdown

| # | Infraction | Class | Min | Expected | Max |
|---|---|---|---|---|---|
| F1 | LSSI 22.2 | Leve | 0 | … | 30,000 |
| … | | | | | |
| **Total** | | | **…** | **…** | **…** |

Notes:
- Expected total is not strictly additive: related infractions are often handled in one procedure.
- Reductions available: <e.g. Spain: up to 40% for acknowledgment + voluntary payment>.
- Exposure not quantified: <items with unverified national amounts or no enforcement precedent>.
- Not included: lawyer fees, civil damages claims, competitor actions, remediation cost.

## Recommended order of fixes
1. <quick wins first: prior blocking, reject button, privacy policy completion>
2. …
```

Keep the chat summary after writing the file to 3–5 lines: overall status, top 3 risks, expected total with min–max range, and the path of the report.
