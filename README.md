# eu-legal-compliance-audit

Agent skill that audits a software project for EU legal compliance gaps (GDPR, cookies/ePrivacy, legal notice, consumer and e-commerce rules, EAA accessibility, AI Act, DSA, licenses, basic security) and estimates the sanction exposure in the owner's country, with detailed figures for Spain.

## Install

```bash
npx skills add PabloViniegra/eu-legal-compliance-audit
```

Add `-g` to install it for your user instead of the current project.

## Contents

```
skills/eu-legal-compliance-audit/
├── SKILL.md                    workflow and principles
├── references/                 controls catalog, fines (Spain, EU), report template
└── scripts/scan_project.py     dependency-free heuristic scanner (Python 3)
```

The output is a technical pre-audit, not legal advice.

## Development

```bash
uvx pytest tests
```
