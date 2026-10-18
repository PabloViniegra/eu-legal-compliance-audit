---
name: eu-legal-compliance-audit
description: Audit a website, web app, SaaS, e-commerce or mobile backend for EU legal compliance gaps that lead to fines — privacy policy and GDPR notices, cookie consent and prior blocking, legal notice/Impressum, terms, third-party services and international transfers, consumer and e-commerce rules, marketing emails, accessibility (EAA), AI Act transparency, DSA, open-source licenses and basic security — and estimate the sanction exposure in the user's country. Use whenever the user asks for a legal, GDPR/RGPD, cookies, LSSI, privacy or compliance review, asks whether their web "cumple la normativa", wants to avoid fines or complaints to an authority, or is launching to EU users — even for one item such as "check my cookie banner" or "do I need a privacy policy".
---

# EU Legal Compliance Audit

This skill reviews a codebase (and, if reachable, the deployed site) for the legal elements that EU and national law require of an online service, explains each gap in plain language, and ends with an **estimated cost of sanctions** in the user's country.

It is a technical pre-audit, not legal advice. Its value is catching the cheap, common, fineable mistakes (no privacy policy, analytics firing before consent, missing legal notice, pre-ticked boxes, undisclosed US processors) before a user complaint or an authority does. Say this once in the report, briefly, and do not hedge every sentence.

## Workflow

### 1. Scope the project (applicability gates)

Most obligations only apply in certain situations, and flagging irrelevant ones destroys the report's credibility. Before evaluating controls, establish these facts — infer them from the code first, then ask the user only for what remains unknown (one short message, at most 4 questions; if no one is there to answer, assume the conservative option and state the assumption at the top of the report):

| Gate | Why it matters | How to infer |
|---|---|---|
| **Country of establishment** of the owner (and main target countries) | Decides the national law, authority and fine amounts | Legal notice text, i18n default locale, TLD, currency, VAT/NIF format, address in footer |
| **Company size** (employees, annual turnover) — micro (<10 & ≤€2M), small, medium, large (>250 or >€50M) | Expected fines scale with size; EAA services exempt microenterprises; some DSA duties exempt micro/small; Spain's Ley 10/2025 applies to large companies | Ask; it can't be read from code |
| **Audience**: B2C (consumers) or B2B only | Consumer law, withdrawal, price rules only apply to B2C | Checkout flows, pricing pages, "for teams" copy |
| **Sells online / subscriptions** | E-commerce controls | Stripe/PayPal/cart/checkout/plan routes |
| **Collects personal data** (forms, accounts, analytics, logs) | GDPR controls | Forms, auth, DB schemas, analytics |
| **User-generated content** shared with others, or marketplace | DSA controls | Comments, uploads, reviews, profiles, seller listings |
| **AI features** (chatbots, generated text/images) | AI Act Art. 50 + data sent to AI providers | OpenAI/Anthropic/Gemini SDKs, chat widgets |
| **Minors** likely among users | Age of consent (14 in Spain, 13–16 elsewhere), DSA Art. 28 | Education/gaming domain, birthdate fields |
| **Sector**: finance, energy, telecoms, transport, health, public sector | Sector law and higher scrutiny | Domain knowledge of the project |

### 2. Run the scanner

```bash
python3 <skill-dir>/scripts/scan_project.py <project-root> --out /tmp/legal_scan.json
```

It is a dependency-free heuristic scanner. It reports, with `file:line` evidence: legal pages and routes found, consent-management platforms, third-party services and trackers (with their usual vendor country), cookie/storage writes, personal-data form fields, pre-ticked consent boxes, AI SDK usage, e-commerce and UGC signals, basic accessibility signals, committed secrets, and copyleft licenses in `node_modules`.

Treat its output as **leads, not verdicts**. A regex can't tell whether Google Analytics is loaded only after consent; you must open the relevant files and read the loading logic. Likewise "no privacy page found" may mean the policy lives in a CMS, a hosted page or a different repo — check links in the footer/layout components before concluding it is missing.

### 3. Check the live site if possible

If the user gives a URL and you have a browser or WebFetch, verify what the code can't show: whether non-essential cookies/requests appear **before** interacting with the banner, whether "Reject" is on the first layer, and whether legal pages actually render. Note in the report which findings were verified live and which come only from code.

### 4. Evaluate the controls

Read `references/controls.md`. It is the catalog of controls grouped by area (legal notice, privacy, cookies, terms, e-commerce/consumer, marketing, accessibility, AI, DSA, security, licenses), each with: legal basis, applicability gate, what to look for in code, pass/fail criteria, and the infraction it maps to for fine estimation.

For each control that applies, assign one status:

- **FAIL** — evidence that the requirement is not met
- **PARTIAL** — exists but incomplete or defective (e.g. privacy policy without international transfers)
- **PASS** — evidence that it is met
- **MANUAL** — can't be determined from code/site (e.g. signed DPAs with processors, records of processing); list it in a short "verify manually" section, never count it in the cost
- **N/A** — gate not met; mention N/A areas in one line, not one row each

Every FAIL/PARTIAL needs concrete evidence (file:line, URL, or the absence verified in the layout/footer) and a concrete fix aimed at a developer (component to add, script to gate, text to include). Generic advice like "ensure GDPR compliance" is useless to the reader.

When the same root cause triggers several controls (e.g. GTM loaded unconditionally → analytics and ads cookies before consent), report it as one finding with the controls it breaks, and count one infraction for costing.

### 5. Estimate the cost of sanctions

Read the fines reference for the user's country:

- Spain → `references/fines-spain.md`
- Any other EU/EEA country → `references/fines-eu.md` (EU-wide ceilings + national notes). If web search is available, look up the national regime for cookies/e-privacy, consumer protection and accessibility, because those amounts are set nationally; if not, use EU ceilings where they exist and mark national figures as "not verified".

Method (explain it briefly in the report so the number is defensible):

1. Map each FAIL/PARTIAL finding to **one infraction** (law + article + national severity class).
2. For each infraction give three figures:
   - **Minimum**: what can realistically happen at best — a warning/apercibimiento with no fine where the law allows it for first-time, corrected infractions, otherwise the legal minimum.
   - **Expected**: the amount authorities typically impose on an organisation of this size for this conduct (use the "observed practice" tables), adjusted up for aggravating factors (many users affected, long duration, sensitive data, minors, intent, repeat) and down for mitigating ones (small size, quick correction).
   - **Legal maximum**: the statutory ceiling for that severity class.
3. Sum each column. Explain that the expected total is not strictly additive (authorities often group related infractions into one procedure) and that the maximum is a theoretical worst case, not a forecast.
4. Mention payment reductions if the country has them (Spain: up to 40% for acknowledgment + voluntary payment).
5. State what is **not** included: lawyer fees, civil damages claims by users (GDPR Art. 82), competitor or consumer-association actions, remediation cost, reputational impact.

Present money in the local currency, rounded sensibly (no false precision like €3,247.18). Clarify that these are mostly **administrative sanctions** opened after a complaint ("denuncia/reclamación") or an inspection, rather than a lawsuit — users often say "demanda" for both.

### 6. Write the report

Use the template in `references/report-template.md`. Write the report in the language the user is speaking to you (the skill files are in English, the report need not be). Default deliverable: a Markdown file `LEGAL_AUDIT.md` at the project root unless the user asks for another format. Then give a 3–5 line summary in chat: overall status, the top 3 risks, and the expected-cost total with its range.

Order findings by **risk = likelihood of complaint × expected fine**, not by area. Cookie consent and privacy-notice failures on a public site are the most complained-about issues in practice, so they usually lead.

## Principles

- **Evidence over assumption.** Every finding cites where it was observed. If you could not check something, it is MANUAL, not FAIL.
- **Applicability first.** A B2B internal tool does not need a withdrawal button; a static portfolio without analytics may legitimately need no cookie banner. Saying so is part of a good audit.
- **Dates matter.** Several obligations are recent or in transition (EAA since 28 Jun 2025, AI Act Art. 50 since 2 Aug 2026, withdrawal function since 19 Jun 2026 with uneven national transposition). The references carry a "last verified" date; if web search is available and an item is marked time-sensitive, re-check its status before reporting it as enforceable.
- **Proportionate tone.** The goal is to help the user fix things, not to scare them. Give the real numbers, including the reassuring ones (most SME fines in Spain for cookie or privacy-notice failures are in the low thousands, and first-time minor LSSI infractions often end in a warning if corrected).
- **Not legal advice.** One sentence in the report recommending review by a lawyer or DPO for anything with high exposure (sensitive data, minors, large user base, AI decisions about people).
