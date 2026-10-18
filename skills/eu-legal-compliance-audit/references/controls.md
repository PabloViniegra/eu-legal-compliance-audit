# Controls catalog

Last verified: 2026-10-18. Items marked ⏱ are time-sensitive; re-check their status if web search is available.

Each control lists: **Basis** (EU law → Spanish transposition where relevant), **Applies when**, **Look for**, **Pass when**, and **Infraction key** (used in the fines references to find amounts).

## Contents
1. Legal notice / provider identification (LEG)
2. Privacy and personal data (PRV)
3. Cookies and device storage (CK)
4. Terms of service (TOS)
5. E-commerce and consumer protection (EC)
6. Commercial communications (MKT)
7. Accessibility (ACC)
8. Artificial intelligence (AI)
9. Digital Services Act (DSA)
10. Security (SEC)
11. Open-source and content licenses (LIC)
12. Out of code scope — verify manually (MAN)

---

## 1. Legal notice / provider identification (LEG)

### LEG-01 Legal notice (Aviso legal / Impressum / Mentions légales)
- **Basis**: e-Commerce Directive 2000/31 Art. 5 → Spain LSSI Art. 10.
- **Applies when**: any website or app run as an economic activity (includes ads-funded blogs, SaaS, freelancers' sites). A purely personal, non-commercial site is outside LSSI.
- **Look for**: page/route `aviso-legal`, `legal-notice`, `impressum`, `mentions-legales`; link in footer/layout on every page.
- **Pass when** it shows: legal name, tax ID (NIF/CIF/VAT), registered address, contact email (a working one, not a form only), trade-register data if a company, professional body/title and authorisation if a regulated profession.
- **Infraction key**: `LSSI-10`.

---

## 2. Privacy and personal data (PRV)

### PRV-01 Privacy policy exists and is reachable
- **Basis**: GDPR Arts. 12–14.
- **Applies when**: any personal data is processed — forms, accounts, analytics with IP/IDs, server logs, newsletters, payment, support chat. In practice almost every site.
- **Look for**: route/page `privacy`, `privacidad`, `politica-de-privacidad`, `datenschutz`; link in footer and at every data collection point (signup, contact, checkout).
- **Pass when** reachable in ≤2 clicks from every page and linked at each form.
- **Infraction key**: `GDPR-13`.

### PRV-02 Privacy policy content (Art. 13/14 checklist)
- **Look for** in the policy text: controller identity + contact; DPO contact if one is required; purposes **and** legal basis per purpose; legitimate interests described if relied on; recipients/categories of recipients (**name the external services** — hosting, analytics, email, payments, CRM, AI APIs); international transfers and safeguard (EU-US Data Privacy Framework, SCCs); retention periods per purpose; data subject rights + how to exercise them; right to complain to the authority (Spain: AEPD); whether providing data is mandatory; automated decision-making/profiling; source of data if not collected from the user (Art. 14).
- **Cross-check against the scanner**: every third-party service detected in code that receives personal data must appear in the policy. Undisclosed processors are the most common PARTIAL.
- **Pass when** every element applicable to the project is present and consistent with what the code actually does.
- **Infraction key**: `GDPR-13`.

### PRV-03 Information at the point of collection and consent mechanics
- **Basis**: GDPR Arts. 7, 13; Spain LOPDGDD Art. 11 (layered information: first layer next to the form with controller, purpose, rights, link to full policy).
- **Look for**: forms with email/phone/name fields; nearby text and link; consent checkboxes.
- **Fail signals**: pre-ticked consent boxes; one checkbox bundling terms + privacy + marketing; marketing consent required to submit a form that doesn't need it; no information near the form.
- **Note**: for contracts or answering a request, consent isn't the legal basis — a checkbox "I have read the privacy policy" is not required by law; the information is. Don't fail a form for lacking a checkbox if the information is there.
- **Infraction key**: `GDPR-7` (consent defects) or `GDPR-13` (missing information).

### PRV-04 Data minimisation
- **Basis**: GDPR Art. 5(1)(c).
- **Look for**: required fields that aren't needed for the purpose (DNI/ID number on a newsletter, birthdate on a contact form, phone mandatory without reason); logging of full request bodies with personal data; analytics capturing form inputs (session replay without masking).
- **Infraction key**: `GDPR-5`.

### PRV-05 Data subject rights in practice
- **Basis**: GDPR Arts. 15–22.
- **Look for**: account deletion feature (or documented process), data export, working contact address for rights requests; soft-delete that never purges.
- **Infraction key**: `GDPR-12-22`.

### PRV-06 Minors
- **Basis**: GDPR Art. 8; Spain LOPDGDD Art. 7 (own consent from 14).
- **Applies when**: service may be used by minors and relies on consent.
- **Look for**: age gate, parental consent flow, birthdate field validation.
- **Infraction key**: `GDPR-8`.

### PRV-07 Third-party services and international transfers
- **Basis**: GDPR Arts. 28, 44–49.
- **Look for**: scanner's `third_party_services` list. For each: does it receive personal data (IP counts)? Is it outside the EEA (US vendors mostly)? Is it disclosed in the policy with its transfer safeguard?
- **Specific case — fonts and CDNs**: loading Google Fonts, or scripts from public CDNs, sends visitors' IPs to a third party without need; a German court (LG München, 2022) awarded damages for this. Recommend self-hosting fonts. Severity low but trivially fixable.
- **Infraction key**: `GDPR-44` (unlawful transfer) or `GDPR-13` (only undisclosed).

### PRV-08 Data protection by design: security of processing
- **Basis**: GDPR Arts. 25, 32.
- **Look for**: see SEC controls; plus passwords stored in plaintext or with fast hashes (MD5/SHA1), personal data in URLs/query strings, PII in logs, unencrypted backups committed.
- **Infraction key**: `GDPR-32`.

---

## 3. Cookies and device storage (CK)

Scope note: the rule covers **any** storage of or access to information on the user's device — cookies, `localStorage`, `sessionStorage`, IndexedDB, fingerprinting, tracking pixels. Strictly necessary storage (session, cart, load balancing, security, the consent choice itself, user-requested preferences like language) is exempt. Analytics is **not** exempt in Spain or most countries (narrow exceptions exist for some configured first-party analytics in France; don't assume them elsewhere). Cookieless tools (Plausible, Umami, Fathom, Matomo configured without cookies) may not need consent for storage, but still need a privacy policy mention.

### CK-01 Consent banner when non-exempt storage exists
- **Basis**: ePrivacy Directive 2002/58 Art. 5(3) → Spain LSSI Art. 22.2; AEPD Cookie Guide (2023 version aligned with EDPB).
- **Look for**: scanner's `consent_platforms`; custom banner components; Google Consent Mode calls.
- **Pass when** non-exempt storage exists **and** a consent mechanism is present. If no non-exempt storage exists, CK is N/A — say so explicitly (a banner is not mandatory just for having a website).
- **Infraction key**: `LSSI-22.2`.

### CK-02 Prior blocking
- **Look for**: analytics/ads/pixel scripts in `<head>`/layout/`index.html`/`_document`/`nuxt.config`/`next.config`/GTM containers loaded unconditionally; `gtag('config', ...)` called before consent; Consent Mode default not set to `denied`; scripts with `type="text/plain" data-category=...` (CMP blocking pattern = good sign).
- **Pass when** no non-exempt script runs and no non-exempt storage is written until the user accepts that category. Verify live if possible (DevTools → Application → Cookies, Network on first load).
- **This is the single most-sanctioned cookie failure.** Treat as FAIL even if a banner exists.
- **Infraction key**: `LSSI-22.2`.

### CK-03 Reject as easy as accept
- **Pass when** the first layer offers "Reject all" (or equivalent) with the same prominence as "Accept all" — same level, same visual weight, no extra clicks. Closing the banner or continuing to browse is not consent.
- **Fail signals**: only "Accept" + "Settings"; reject hidden in second layer; pre-activated toggles in settings; "legitimate interest" toggles for tracking enabled by default.
- **Infraction key**: `LSSI-22.2`.

### CK-04 Granularity and withdrawal
- **Pass when** consent can be given per purpose (analytics, personalisation, advertising) and withdrawn at any time as easily as given — persistent link/icon ("Cookie settings") in the footer.
- **Infraction key**: `LSSI-22.2`.

### CK-05 Cookie policy
- **Pass when** it lists cookies/storage used (can be grouped), purpose, first or third party (naming the third parties), duration, and how to withdraw consent; consistent with what the code actually sets.
- **Infraction key**: `LSSI-22.2`.

### CK-06 Consent record and renewal
- **Look for**: consent stored with timestamp/version; re-prompt when purposes change. AEPD recommends not keeping a consent choice longer than 24 months.
- **Infraction key**: `LSSI-22.2` (usually low weight; mention as improvement).

### CK-07 Cookie walls
- **Fail signal**: content blocked unless all cookies accepted, without a genuine alternative (AEPD admits a paid/alternative access option in some cases; still flag for review).
- **Infraction key**: `LSSI-22.2`.

---

## 4. Terms of service (TOS)

### TOS-01 Terms / conditions of use exist and are accepted
- **Basis**: contract law; for consumers, TRLGDCU (Spain) and Unfair Terms Directive 93/13; e-Commerce Directive Art. 10 (information on contracting steps, language, archiving).
- **Applies when**: accounts, paid services, marketplaces, UGC, APIs. A purely informational site needs only the legal notice.
- **Look for**: `terms`, `terminos`, `condiciones`, `tos`, `agb`; acceptance at signup/checkout; stored acceptance (user id, version, timestamp) in DB schema.
- **Pass when** terms exist, are presented before contracting, acceptance is recorded with version, and they can be stored/printed by the user.
- **Infraction key**: `CONSUMER-INFO` (B2C) — B2B only: no fine, contractual risk; mark as risk without cost.

### TOS-02 Obviously unfair clauses (B2C)
- **Look for in text**: jurisdiction outside the consumer's domicile, unilateral changes without notice/right to terminate, total exclusion of liability, automatic renewal hidden, waiver of withdrawal right.
- **Infraction key**: `CONSUMER-UNFAIR`.

---

## 5. E-commerce and consumer protection (EC) — B2C only

### EC-01 Pre-contractual information
- **Basis**: Consumer Rights Directive 2011/83 Arts. 6, 8 → TRLGDCU Arts. 97–98.
- **Pass when** before ordering the user sees: main characteristics, total price **including taxes**, delivery costs, payment and delivery terms, duration and cancellation of subscriptions, legal guarantee, withdrawal right, trader identity.
- **Infraction key**: `CONSUMER-INFO`.

### EC-02 Order button labelling
- **Basis**: CRD Art. 8(2).
- **Pass when** the final button says "Order with obligation to pay" / "Pedido con obligación de pago" / "Comprar y pagar" or equally unambiguous wording. "Continue", "Submit", "Confirm" fail.
- **Infraction key**: `CONSUMER-INFO`.

### EC-03 Right of withdrawal information
- **Pass when** the 14-day right, conditions, exceptions (e.g. digital content once download starts with consent) and the model withdrawal form are provided.
- **Infraction key**: `CONSUMER-INFO`.

### EC-04 ⏱ Withdrawal function ("botón de desistimiento")
- **Basis**: Directive 2023/2673 (new Art. 11a CRD), applicable from 19 Jun 2026.
- **Applies when**: contracts concluded online with a right of withdrawal (goods, services, subscriptions, digital content, financial services).
- **Pass when** a clearly labelled function ("Withdraw from contract here" / "Desistir del contrato aquí") is permanently available during the withdrawal period, collects the minimal identification data, has a confirmation step, and sends an acknowledgement on a durable medium (email).
- **Status note**: Spain had not transposed the Directive as of mid-2026 (OCU complaint, 19 Jun 2026). Without a national law, a national authority can't directly fine for this specific duty, but courts must interpret national law in its light and transposition may happen any time. Report as FAIL with "fine exposure: pending national transposition" unless verification shows it has been transposed. Check other countries individually.
- **Infraction key**: `CONSUMER-WITHDRAWAL-FN`.

### EC-05 Order confirmation on durable medium
- **Look for**: transactional email after purchase including terms and withdrawal info.
- **Infraction key**: `CONSUMER-INFO`.

### EC-06 Subscriptions and cancellation
- **Pass when** cancellation is possible online through the same channel used to subscribe, without obstacles; renewal and price changes are disclosed. Spain: TRLGDCU Art. 62.3 forbids obstructive cancellation conditions.
- **Infraction key**: `CONSUMER-UNFAIR`.

### EC-07 Legal guarantee
- **Pass when** terms/product pages state the legal guarantee (Spain: 3 years for goods, 2 years for digital content/services, since 2022).
- **Infraction key**: `CONSUMER-INFO`.

### EC-08 Price reductions and reviews (Omnibus Directive 2019/2161)
- **Look for**: "was/now" prices, discount badges — the reference "before" price must be the lowest price of the previous 30 days. Reviews: state whether and how they are verified; no fake reviews.
- **Infraction key**: `CONSUMER-UNFAIR`.

### EC-09 Dark patterns
- **Basis**: Unfair Commercial Practices Directive 2005/29; DSA Art. 25 (platforms).
- **Look for**: fake countdown timers (timers that reset), fake low-stock messages, confirmshaming, pre-selected add-ons (insurance, donations) — pre-ticked paid extras are expressly prohibited by CRD Art. 22.
- **Infraction key**: `CONSUMER-UNFAIR`.

### EC-10 Stale ODR link
- The EU ODR platform was discontinued on 20 Jul 2025 (Regulation 2024/3228). A link to it is no longer required; if present, recommend removing it (dead link). Do not FAIL a site for missing it. ADR information is still required if the trader adheres to an ADR body.
- **Infraction key**: none.

### EC-11 Spain — customer service law (Ley 10/2025) ⏱
- **Applies when**: company established/operating in Spain that is large (>250 employees or >€50M turnover) or provides basic services of general interest (energy, water, transport, telecoms, postal, financial). Adaptation deadline 28 Dec 2026.
- **Look for**: support channels — right to a human (automated-only support is prohibited), published customer-service info on the web.
- **Infraction key**: `CONSUMER-INFO` (sanctioned under consumer law).

---

## 6. Commercial communications (MKT)

### MKT-01 Marketing emails/SMS
- **Basis**: ePrivacy Art. 13 → LSSI Arts. 20–21.
- **Look for**: newsletter signups, mailing libs (Mailchimp, SendGrid, Brevo, Resend, nodemailer used for campaigns), marketing flags in user schema.
- **Pass when** prior specific consent is collected (or soft opt-in: existing customer, similar products, opportunity to refuse at collection and in each message), every message has a working unsubscribe, and messages identify the sender and are identifiable as advertising.
- **Infraction key**: `LSSI-21`.

---

## 7. Accessibility (ACC)

### ACC-01 ⏱ EAA scope
- **Basis**: European Accessibility Act, Directive 2019/882 → Spain Ley 11/2023 (obligations applicable from 28 Jun 2025; existing services have transition until 28 Jun 2030 in some cases).
- **Applies when**: consumer e-commerce services, banking services, e-books, passenger transport services, electronic communications, audiovisual access services — offered by non-micro enterprises (services provided by microenterprises are exempt). Public-sector sites are under the Web Accessibility Directive instead (Spain RD 1112/2018).
- If not in scope, ACC findings are recommendations (good practice, discrimination-law risk) with no fine estimate.

### ACC-02 WCAG 2.1 AA signals (EN 301 549)
- **Look for (static signals only)**: `<html lang>` missing; `<img>` without `alt`; inputs without labels; buttons/links without accessible name (icon-only); `outline: none` without replacement focus style; autoplay media; text in images; low-contrast tokens if design tokens are readable.
- Static analysis can't certify accessibility; recommend axe/Lighthouse/pa11y run and manual keyboard + screen-reader test.
- **Infraction key**: `ACCESSIBILITY`.

### ACC-03 Accessibility information/statement
- **Pass when** the service publishes how it meets accessibility requirements (EAA Annex V) — typically an accessibility statement page.
- **Infraction key**: `ACCESSIBILITY`.

---

## 8. Artificial intelligence (AI)

### AI-01 ⏱ Chatbot / AI interaction disclosure
- **Basis**: AI Act (Reg. 2024/1689) Art. 50(1), applicable since 2 Aug 2026 (not deferred by the 2026 Digital Omnibus).
- **Applies when**: users interact with an AI system (chat assistant, AI voice, AI email replies) and it isn't obvious.
- **Pass when** users are told they are interacting with AI at the latest at first interaction.
- **Infraction key**: `AIACT-50`.

### AI-02 ⏱ Marking of AI-generated content and deepfakes
- **Basis**: AI Act Art. 50(2) (providers: machine-readable marking of synthetic audio/image/video/text — the Omnibus gave a transition for some existing systems; verify) and Art. 50(4) (deployers: disclose deepfakes and AI-generated text published to inform the public, unless human-reviewed under editorial responsibility).
- **Infraction key**: `AIACT-50`.

### AI-03 High-risk and prohibited uses
- **Look for**: AI used to score/rank people for hiring, credit, education access, insurance pricing, biometric identification, emotion recognition at work/school.
- Prohibited practices (Art. 5) apply since Feb 2025. Standalone high-risk obligations (Annex III) were postponed to 2 Dec 2027 by the Digital Omnibus — flag as "upcoming" with a recommendation, not as a current fine.
- **Infraction key**: `AIACT-5` (prohibited) / none yet for high-risk.

### AI-04 Personal data sent to AI providers
- **Look for**: prompts that include user data sent to OpenAI/Anthropic/Google/Mistral APIs; whether the provider is disclosed as processor, transfer safeguard, retention/training opt-out configured.
- **Infraction key**: `GDPR-13` / `GDPR-44`.

---

## 9. Digital Services Act (DSA)

- **Basis**: Regulation 2022/2065, applicable to all intermediary services since 17 Feb 2024. Spain's Digital Services Coordinator is the CNMC.
- **Applies when**: the service stores and shares user content (hosting, forums, comments, reviews, marketplaces, social features). Micro and small enterprises are exempt from the online-platform and marketplace duties (Arts. 20–32, except publishing user numbers under Art. 24(3)), but not from Arts. 11–18.

| ID | Requirement | Article |
|---|---|---|
| DSA-01 | Single point of contact for authorities and for users (email/form), published | 11, 12 |
| DSA-02 | Terms explain content moderation rules, tools, complaint handling | 14 |
| DSA-03 | Notice-and-action: anyone can report illegal content electronically | 16 |
| DSA-04 | Statement of reasons to users whose content is removed/restricted | 17 |
| DSA-05 | (Platforms, not micro/small) internal complaint system; no dark patterns; ad labelling with "why am I seeing this"; no profiling ads to minors | 20, 25, 26, 28 |
| DSA-06 | (Marketplaces, not micro/small) trader traceability (KYBC) | 30 |

- **Infraction key**: `DSA`.

---

## 10. Security (SEC)

Security failures feed GDPR Art. 32 and become very expensive after a breach.

| ID | Check | Look for |
|---|---|---|
| SEC-01 | No secrets in the repo | API keys, private keys, `.env` committed, credentials in config (scanner `secrets`) |
| SEC-02 | HTTPS enforced, HSTS | redirects, security headers config (helmet, nginx, vercel.json, Flask-Talisman) |
| SEC-03 | Password storage | bcrypt/argon2/scrypt vs md5/sha1/plain |
| SEC-04 | PII in logs | logging of request bodies, emails, tokens |
| SEC-05 | Breach handling | any incident/72h notification process documented (often MANUAL) |

- **Infraction key**: `GDPR-32`.

---

## 11. Open-source and content licenses (LIC)

Not administrative fines, but a source of claims and forced code disclosure — report as legal risk without a fine estimate.

| ID | Check |
|---|---|
| LIC-01 | Copyleft dependencies: AGPL in a network service obliges offering source to users; GPL in distributed apps/binaries obliges source distribution. Scanner lists GPL/AGPL/SSPL packages found in `node_modules`; check Python/Go manifests manually or with `pip-licenses` / `go-licenses`. |
| LIC-02 | Attribution: MIT/BSD/Apache notices preserved in distributed bundles (third-party notices page for mobile/desktop apps). |
| LIC-03 | Fonts, icons, images, stock photos with license proof; no scraped images. |

---

## 12. Out of code scope — verify manually (MAN)

List these briefly in the report's "verify manually" section; never count them in the cost.

- Records of processing activities (GDPR Art. 30) — exemption for <250 employees is narrow (not if processing is regular).
- Data processing agreements (Art. 28) signed with every processor detected.
- DPIA for high-risk processing (large-scale monitoring, sensitive data, AI profiling).
- DPO appointment where mandatory (Spain: LOPDGDD Art. 34 list — e.g. education centres, e-commerce/advertising profiling at large scale, health, insurance).
- Breach register and procedure.
- Spain: whistleblowing channel (Ley 2/2023) for companies with ≥50 employees.
- Payment security (PCI DSS) if card data touches own servers (prefer hosted checkout).
- NIS2 if in a covered sector and medium/large.
