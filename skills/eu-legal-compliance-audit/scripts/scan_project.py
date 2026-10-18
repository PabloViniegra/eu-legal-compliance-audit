#!/usr/bin/env python3
"""
Heuristic legal-compliance scanner for a software project.

Walks a project directory and reports *leads* (with file:line evidence) for:
legal pages/routes, consent-management platforms, third-party services and
trackers, cookie/storage writes, personal-data form fields, pre-ticked consent
boxes, AI SDK usage, e-commerce/UGC/marketing signals, basic accessibility
signals, committed secrets, and copyleft licenses in node_modules.

No dependencies. Output: JSON (stdout or --out file).

Usage:
    python3 scan_project.py <project-root> [--out scan.json] [--max-evidence 8]

The output is a starting point for human/LLM review, not a verdict: a regex
cannot tell whether a script is loaded only after consent.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".nuxt", ".output", "out",
    "coverage", ".venv", "venv", "env", "__pycache__", ".pytest_cache", "vendor",
    ".turbo", ".cache", ".svelte-kit", "target", ".idea", ".vscode", "storybook-static",
}
TEXT_EXT = {
    ".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte",
    ".astro", ".py", ".go", ".rb", ".php", ".java", ".kt", ".cs", ".rs", ".md", ".mdx",
    ".json", ".yaml", ".yml", ".toml", ".env", ".txt", ".jinja", ".jinja2", ".j2",
    ".twig", ".erb", ".ejs", ".hbs", ".liquid", ".njk", ".xml", ".ini", ".cfg", ".conf",
    ".tf", ".sql", ".prisma", ".graphql", ".css", ".scss",
}
TEXT_NAMES = {"Dockerfile", ".env", ".env.local", ".env.production", "Procfile", "go.mod",
              "requirements.txt", "Pipfile", "package.json", "pyproject.toml"}
MAX_FILE_BYTES = 1_500_000
# Project docs often mention legal pages as TODOs; counting them would hide a missing page.
PROJECT_DOCS = re.compile(r"^(readme|changelog|contributing|todo|history|code_of_conduct|security)\b", re.I)

# ---------------------------------------------------------------- patterns

LEGAL_PAGES = {
    "legal_notice": r"aviso[-_ ]?legal|legal[-_ ]?notice|impressum|mentions[-_ ]?l[eé]gales|note[-_ ]?legali",
    "privacy_policy": r"privacy[-_ ]?policy|pol[ií]tica[-_ ]?de[-_ ]?privacidad|/privacy\b|privacidad|datenschutz|confidentialit[eé]|informativa[-_ ]?privacy",
    "cookie_policy": r"cookie[-_ ]?policy|pol[ií]tica[-_ ]?de[-_ ]?cookies|/cookies\b|cookie[-_ ]?richtlinie",
    "terms": r"terms[-_ ]?(of[-_ ]?(service|use)|and[-_ ]?conditions)|\btos\b|t[eé]rminos|condiciones[-_ ]?(generales|de[-_ ]?uso|de[-_ ]?contrataci[oó]n)|\bagb\b|cgv|cgu",
    "accessibility_statement": r"accessibility[-_ ]?statement|declaraci[oó]n[-_ ]?de[-_ ]?accesibilidad|/accessibility\b|/accesibilidad\b|barrierefreiheit",
    "withdrawal_returns": r"desistimiento|withdraw(al)?[-_ ]?(form|from|right|function)|right[-_ ]?of[-_ ]?withdrawal|returns?[-_ ]?policy|devoluciones|widerruf",
    "cookie_settings_link": r"cookie[-_ ]?(settings|preferences|preferencias|configuraci[oó]n)|manage[-_ ]?cookies|gestionar[-_ ]?cookies",
}

CONSENT_PLATFORMS = {
    "Cookiebot": r"cookiebot",
    "OneTrust": r"onetrust|otSDKStub|optanon",
    "Didomi": r"didomi",
    "iubenda": r"iubenda",
    "CookieYes": r"cookieyes|cookie-law-info",
    "Klaro": r"\bklaro\b",
    "vanilla-cookieconsent": r"vanilla-cookieconsent|orestbida|CookieConsent\.run|cookieconsent\.run",
    "Osano": r"osano",
    "Complianz": r"complianz",
    "Usercentrics": r"usercentrics",
    "Termly": r"termly",
    "tarteaucitron": r"tarteaucitron",
    "Quantcast Choice": r"quantcast.*choice|cmp\.quantcast",
    "Axeptio": r"axeptio",
    "Google Consent Mode": r"gtag\(\s*['\"]consent['\"]",
    "TCF API": r"__tcfapi",
    "Generic consent component": r"cookie[-_]?(banner|consent|notice)|consent[-_]?(banner|manager|modal)",
}

# name: (regex, category, vendor_country, needs_consent_default)
SERVICES = {
    "Google Tag Manager": (r"googletagmanager\.com/gtm|GTM-[A-Z0-9]{4,}", "tag manager", "US", "depends"),
    "Google Analytics": (r"google-analytics\.com|googletagmanager\.com/gtag|gtag\(\s*['\"]config['\"]|\bG-[A-Z0-9]{6,}\b|UA-\d{4,}-\d+|react-ga|vue-gtag|@next/third-parties", "analytics", "US", "yes"),
    "Google Ads / DoubleClick": (r"googleadservices|doubleclick\.net|googlesyndication|AW-\d{6,}|adsbygoogle", "advertising", "US", "yes"),
    "Meta Pixel": (r"connect\.facebook\.net|fbq\(|facebook-pixel|react-facebook-pixel", "advertising", "US", "yes"),
    "LinkedIn Insight": (r"snap\.licdn\.com|_linkedin_partner_id", "advertising", "US", "yes"),
    "TikTok Pixel": (r"analytics\.tiktok\.com|ttq\.", "advertising", "CN/SG/US", "yes"),
    "X/Twitter Pixel": (r"static\.ads-twitter\.com|twq\(", "advertising", "US", "yes"),
    "Hotjar": (r"hotjar", "session replay/analytics", "MT(EU)", "yes"),
    "Microsoft Clarity": (r"clarity\.ms", "session replay/analytics", "US", "yes"),
    "Mixpanel": (r"mixpanel", "analytics", "US", "yes"),
    "Amplitude": (r"amplitude", "analytics", "US", "yes"),
    "Segment": (r"segment\.(com|io)|analytics-next|@segment/", "analytics", "US", "yes"),
    "PostHog": (r"posthog", "analytics", "US/EU (check host)", "yes"),
    "Heap": (r"heapanalytics|heap\.load", "analytics", "US", "yes"),
    "Matomo": (r"matomo|piwik", "analytics", "self-hosted/EU", "depends"),
    "Plausible": (r"plausible\.io|plausible-tracker", "analytics (cookieless)", "EU", "no"),
    "Umami": (r"umami", "analytics (cookieless)", "self-hosted", "no"),
    "Vercel Analytics": (r"@vercel/analytics|@vercel/speed-insights", "analytics", "US", "depends"),
    "Cloudflare Web Analytics": (r"static\.cloudflareinsights\.com", "analytics", "US", "no"),
    "Sentry": (r"sentry", "error monitoring", "US/EU (check region)", "depends"),
    "Datadog RUM": (r"datadog-rum|@datadog/browser", "monitoring", "US/EU (check site)", "depends"),
    "LogRocket": (r"logrocket", "session replay", "US", "yes"),
    "FullStory": (r"fullstory", "session replay", "US", "yes"),
    "Intercom": (r"intercom", "support chat", "US", "depends"),
    "Crisp": (r"crisp\.chat", "support chat", "FR(EU)", "depends"),
    "Zendesk": (r"zendesk|zdassets", "support", "US", "depends"),
    "Tawk.to": (r"tawk\.to", "support chat", "US", "depends"),
    "HubSpot": (r"hubspot|hs-scripts|hsforms", "CRM/marketing", "US", "yes"),
    "Mailchimp": (r"mailchimp|list-manage\.com", "email marketing", "US", "n/a"),
    "SendGrid": (r"sendgrid", "email delivery", "US", "n/a"),
    "Brevo/Sendinblue": (r"brevo|sendinblue|sib-api", "email marketing", "FR(EU)", "n/a"),
    "Resend": (r"\bresend\b", "email delivery", "US", "n/a"),
    "Mailgun": (r"mailgun", "email delivery", "US/EU", "n/a"),
    "Amazon SES": (r"@aws-sdk/client-ses|boto3.*ses|ses\.amazonaws", "email delivery", "US/EU (check region)", "n/a"),
    "Stripe": (r"stripe", "payments", "US/IE", "n/a"),
    "PayPal": (r"paypal", "payments", "US/LU", "n/a"),
    "Redsys": (r"redsys", "payments", "ES", "n/a"),
    "Google reCAPTCHA": (r"recaptcha", "bot protection", "US", "depends"),
    "hCaptcha": (r"hcaptcha", "bot protection", "US", "depends"),
    "Cloudflare Turnstile": (r"turnstile", "bot protection", "US", "no"),
    "YouTube embed": (r"youtube\.com/embed|youtube-nocookie|react-youtube|lite-youtube", "embedded media", "US", "yes (use nocookie + click-to-load)"),
    "Vimeo embed": (r"player\.vimeo\.com", "embedded media", "US", "depends"),
    "Google Maps": (r"maps\.googleapis\.com|google\.com/maps/embed|@react-google-maps|vue2-google-maps", "maps", "US", "yes (click-to-load)"),
    "Google Fonts (remote)": (r"fonts\.googleapis\.com|fonts\.gstatic\.com", "fonts", "US", "self-host recommended"),
    "Public CDN": (r"cdn\.jsdelivr\.net|unpkg\.com|cdnjs\.cloudflare\.com", "CDN", "US", "self-host recommended"),
    "Firebase": (r"firebase", "backend/analytics", "US", "depends"),
    "Supabase": (r"supabase", "backend", "US/EU (check region)", "n/a"),
    "Auth0": (r"auth0", "authentication", "US/EU", "n/a"),
    "Clerk": (r"@clerk/", "authentication", "US", "n/a"),
    "OpenAI": (r"openai", "AI API", "US", "n/a"),
    "Anthropic": (r"@anthropic-ai/|anthropic", "AI API", "US", "n/a"),
    "Google Gemini/Vertex AI": (r"generativelanguage|google-generativeai|@google/generative-ai|@google/genai|vertexai|aiplatform", "AI API", "US/EU (check region)", "n/a"),
    "Mistral": (r"mistralai", "AI API", "FR(EU)", "n/a"),
    "LangChain": (r"langchain", "AI framework", "-", "n/a"),
    "AWS": (r"aws-sdk|@aws-sdk|boto3", "cloud", "US/EU (check region)", "n/a"),
    "Google Cloud": (r"@google-cloud/|google\.cloud|cloud\.google\.com", "cloud", "US/EU (check region)", "n/a"),
    "Vercel": (r"vercel\.json|@vercel/", "hosting", "US", "n/a"),
    "Netlify": (r"netlify", "hosting", "US", "n/a"),
}

COOKIE_WRITES = r"document\.cookie\s*=|localStorage\.setItem|sessionStorage\.setItem|indexedDB\.open|set_cookie\(|\.set_cookie|res\.cookie\(|Set-Cookie|http\.SetCookie|setcookie\(|cookies\(\)\.set|useCookie\(|js-cookie|Cookies\.set\("
PII_FIELDS = r"type=[\"'](email|tel|password|date)[\"']|name=[\"'](e-?mail|phone|telefono|tel[eé]fono|dni|nif|nie|passport|birth|fecha_?nacimiento|address|direcci[oó]n|iban)[\"']|autocomplete=[\"'](email|tel|bday|street-address|cc-number)"
PRETICKED = r"<input[^>]*type=[\"']checkbox[\"'][^>]*\bchecked\b[^>]*>|defaultChecked\s*=\s*\{?\s*true|:checked=[\"']true[\"']|checked\s*=\s*\{\s*true\s*\}"
CONSENT_WORDS = r"consent|consiento|acepto|accept|privac|newsletter|marketing|comercial|publicidad|offers|ofertas"
ECOMMERCE = r"\bcheckout\b|\bcart\b|carrito|add[-_ ]?to[-_ ]?cart|a[ñn]adir al carrito|\border(s)?\b.*(create|place)|subscription|suscripci[oó]n|pricing|precios|\bplan(es)?\b.*(month|mes)"
ORDER_BUTTON = r"pedido con obligaci[oó]n de pago|order with obligation to pay|zahlungspflichtig bestellen|commande avec obligation de paiement|comprar y pagar|pay now|pagar ahora"
UGC = r"\bcomments?\b|comentarios|upload|subir archivo|\breviews?\b|valoraciones|\bposts?\b|forum|foro|marketplace|seller|vendedor|user[-_ ]?profile|perfil p[uú]blico"
MARKETING = r"newsletter|subscribe|suscr[ií]bete|mailing[-_ ]?list|unsubscribe|darse de baja|marketing[-_ ]?consent|opt[-_ ]?in"
AI_DISCLOSURE = r"(eres|est[aá]s).{0,30}(ia|inteligencia artificial)|ai[-_ ]?(assistant|generated|disclosure)|generated by ai|generado por (ia|inteligencia artificial)|you are (talking|chatting) (to|with) an? ai|asistente virtual|chatbot"
AGE = r"birth|nacimiento|edad|\bage\b|minor|menor de|parental"
ACC_HTML_LANG = r"<html(?![^>]*\blang=)[^>]*>"
ACC_IMG_NO_ALT = r"<img(?![^>]*\balt=)(?![^>]*:alt=)[^>]*>"
ACC_OUTLINE_NONE = r"outline\s*:\s*(none|0)\b"

SECRETS = {
    "AWS access key": r"AKIA[0-9A-Z]{16}",
    "Private key": r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----",
    "OpenAI/Anthropic-style key": r"\bsk-(ant-|proj-)?[A-Za-z0-9_\-]{20,}",
    "Stripe live key": r"\b(sk|rk)_live_[A-Za-z0-9]{16,}",
    "Google API key": r"AIza[0-9A-Za-z\-_]{35}",
    "Slack token": r"xox[baprs]-[A-Za-z0-9-]{10,}",
    "Generic password assignment": r"(?i)(password|passwd|secret|api[_-]?key)\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']",
}
COPYLEFT = re.compile(r"\b(AGPL|GPL|LGPL|SSPL|EUPL|OSL|CC-BY-SA)", re.I)
WEAK_HASH = r"md5\(|hashlib\.md5|hashlib\.sha1|createHash\(['\"](md5|sha1)['\"]\)|crypto/md5|crypto/sha1"
GOOD_HASH = r"bcrypt|argon2|scrypt|passlib|werkzeug\.security|pbkdf2"


def compile_map(d):
    return {k: re.compile(v, re.I) for k, v in d.items()}


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".") or d in {".github"}]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in TEXT_EXT or fn in TEXT_NAMES or fn.startswith(".env"):
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(p) <= MAX_FILE_BYTES:
                        yield p
                except OSError:
                    continue


def read_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().splitlines()
    except OSError:
        return []


def committable_files(root):
    """Tracked plus untracked-but-not-ignored files, or None when git is unavailable."""
    try:
        r = subprocess.run(["git", "-C", root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return {f for f in r.stdout.split("\0") if f}


def checkbox_context(lines, idx, match):
    """Text that labels one checkbox: the tag, the text after it up to the next
    input, and any <label for=id>. A fixed line window would attribute a nearby
    newsletter label to an unrelated "remember me" box."""
    line = lines[idx]
    start = line.rfind("<", 0, match.start() + 1)
    head = ""
    if start == -1:  # multi-line JSX tag: walk back to its opening line
        start = 0
        head = "\n".join(lines[max(0, idx - 4): idx])
        head = head[max(0, head.rfind("<")):]
    tail = "\n".join([line[start:]] + lines[idx + 1: idx + 3])
    nxt = tail.find("<input", 1)
    ctx = head + "\n" + (tail if nxt == -1 else tail[:nxt])
    id_m = re.search(r"\bid=[\"'{]+([\w-]+)", ctx)
    if id_m:
        label = re.compile(r"<label[^>]*(?:for|htmlFor)=[\"'{]+%s[\"'}][^>]*>(.*?)</label>" % re.escape(id_m.group(1)), re.I)
        for near in lines[max(0, idx - 3): idx + 4]:
            lm = label.search(near)
            if lm:
                ctx += " " + lm.group(1)
    return ctx


class Collector:
    def __init__(self, root, max_ev):
        self.root = root
        self.max_ev = max_ev
        self.data = defaultdict(lambda: {"count": 0, "evidence": []})

    def add(self, key, path, lineno, line):
        entry = self.data[key]
        entry["count"] += 1
        if len(entry["evidence"]) < self.max_ev:
            rel = os.path.relpath(path, self.root)
            entry["evidence"].append(f"{rel}:{lineno}: {line.strip()[:160]}")

    def get(self, key):
        return self.data.get(key, {"count": 0, "evidence": []})


def scan_paths_for_legal_pages(root, files, pats, col):
    """File/directory names are strong evidence of a legal page or route."""
    for p in files:
        rel = os.path.relpath(p, root).lower()
        for key, rx in pats.items():
            if rx.search(rel):
                col.add(f"legal_pages.{key}", p, 0, "(path) " + rel)


def scan_node_licenses(root, max_items=40):
    found = []
    nm = os.path.join(root, "node_modules")
    if not os.path.isdir(nm):
        return {"checked": False, "copyleft": []}
    for dirpath, dirnames, filenames in os.walk(nm):
        depth = os.path.relpath(dirpath, nm).count(os.sep)
        if depth > 2:
            dirnames[:] = []
            continue
        if "package.json" in filenames:
            try:
                with open(os.path.join(dirpath, "package.json"), encoding="utf-8", errors="ignore") as f:
                    pj = json.load(f)
            except (OSError, ValueError):
                continue
            lic = pj.get("license") or pj.get("licenses")
            lic_s = json.dumps(lic) if not isinstance(lic, str) else lic
            # SPDX "A OR B" lets the user pick; only copyleft if every alternative is.
            alternatives = re.split(r"\s+OR\s+", lic_s.strip("()")) if lic_s else []
            if alternatives and all(COPYLEFT.search(a) for a in alternatives):
                found.append({"package": pj.get("name"), "version": pj.get("version"), "license": lic_s})
                if len(found) >= max_items:
                    break
    return {"checked": True, "copyleft": found}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--out")
    ap.add_argument("--max-evidence", type=int, default=8)
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.exit(f"Not a directory: {root}")

    files = list(iter_files(root))
    col = Collector(root, args.max_evidence)

    legal = compile_map(LEGAL_PAGES)
    cmps = compile_map(CONSENT_PLATFORMS)
    services = {k: (re.compile(v[0], re.I), v[1], v[2], v[3]) for k, v in SERVICES.items()}
    secrets = {k: re.compile(v) for k, v in SECRETS.items()}
    simple = {
        "storage_writes": re.compile(COOKIE_WRITES, re.I),
        "pii_form_fields": re.compile(PII_FIELDS, re.I),
        "ecommerce_signals": re.compile(ECOMMERCE, re.I),
        "order_button_wording_ok": re.compile(ORDER_BUTTON, re.I),
        "ugc_signals": re.compile(UGC, re.I),
        "marketing_signals": re.compile(MARKETING, re.I),
        "ai_disclosure_text": re.compile(AI_DISCLOSURE, re.I),
        "age_signals": re.compile(AGE, re.I),
        "a11y.html_without_lang": re.compile(ACC_HTML_LANG, re.I),
        "a11y.img_without_alt": re.compile(ACC_IMG_NO_ALT, re.I),
        "a11y.outline_removed": re.compile(ACC_OUTLINE_NONE, re.I),
        "security.weak_hash": re.compile(WEAK_HASH, re.I),
        "security.strong_password_hash": re.compile(GOOD_HASH, re.I),
    }
    preticked = re.compile(PRETICKED, re.I)
    consent_words = re.compile(CONSENT_WORDS, re.I)

    scan_paths_for_legal_pages(root, files, legal, col)
    env_files = []
    committable = committable_files(root)

    for p in files:
        base = os.path.basename(p)
        rel = os.path.relpath(p, root)
        # Gitignored files never reach the repository, so they are not secret leaks.
        may_be_committed = committable is None or rel.replace(os.sep, "/") in committable
        if base.startswith(".env") and not base.endswith((".example", ".sample", ".template")) and may_be_committed:
            env_files.append(rel)
        is_doc = p.lower().endswith((".md", ".mdx", ".txt"))
        if is_doc and PROJECT_DOCS.match(base):
            continue
        lines = read_lines(p)
        for i, line in enumerate(lines, 1):
            if len(line) > 5000:
                line = line[:5000]
            for key, rx in legal.items():
                if rx.search(line):
                    col.add(f"legal_pages.{key}", p, i, line)
            if is_doc:
                continue  # docs mention services without using them
            for key, rx in cmps.items():
                if rx.search(line):
                    col.add(f"consent_platforms.{key}", p, i, line)
            for name, (rx, _cat, _cty, _c) in services.items():
                if rx.search(line):
                    col.add(f"services.{name}", p, i, line)
            for key, rx in simple.items():
                if rx.search(line):
                    col.add(key, p, i, line)
            m = preticked.search(line)
            if m and consent_words.search(checkbox_context(lines, i - 1, m)):
                col.add("preticked_consent_checkbox", p, i, line)
            for key, rx in secrets.items():
                if may_be_committed and rx.search(line) and "example" not in line.lower() and "xxxx" not in line.lower():
                    col.add(f"secrets.{key}", p, i, "<redacted match> " + rel)

    # ---------------------------------------------------------------- assemble
    out = {
        "root": root,
        "files_scanned": len(files),
        "legal_pages": {},
        "consent_platforms": {},
        "third_party_services": [],
        "signals": {},
        "accessibility": {},
        "security": {},
        "secrets": {},
        "committed_env_files": env_files,
        "licenses": scan_node_licenses(root),
        "notes": [
            "Leads only: confirm by reading the code (e.g. whether trackers load before consent).",
            "Legal pages may live outside the repo (CMS, hosted policy); check footer links before marking missing.",
            "Service matches by keyword can be false positives (e.g. 'stripe' in CSS class names); verify.",
        ],
    }
    if committable is None:
        out["notes"].append("Not a git repository: env files and secrets are reported even if they would be gitignored.")
    for key in LEGAL_PAGES:
        out["legal_pages"][key] = col.get(f"legal_pages.{key}")
    for key in CONSENT_PLATFORMS:
        e = col.get(f"consent_platforms.{key}")
        if e["count"]:
            out["consent_platforms"][key] = e
    for name, (_rx, cat, cty, consent) in services.items():
        e = col.get(f"services.{name}")
        if e["count"]:
            out["third_party_services"].append({
                "service": name, "category": cat, "usual_vendor_location": cty,
                "consent_needed_default": consent, **e,
            })
    for key in ["storage_writes", "pii_form_fields", "preticked_consent_checkbox", "ecommerce_signals",
                "order_button_wording_ok", "ugc_signals", "marketing_signals", "ai_disclosure_text", "age_signals"]:
        out["signals"][key] = col.get(key)
    for key in ["a11y.html_without_lang", "a11y.img_without_alt", "a11y.outline_removed"]:
        out["accessibility"][key.split(".", 1)[1]] = col.get(key)
    for key in ["security.weak_hash", "security.strong_password_hash"]:
        out["security"][key.split(".", 1)[1]] = col.get(key)
    for key in SECRETS:
        e = col.get(f"secrets.{key}")
        if e["count"]:
            out["secrets"][key] = e

    cats = {s["category"] for s in out["third_party_services"]}
    out["summary"] = {
        "has_tracking_services": any(c in cats for c in ("analytics", "advertising", "session replay/analytics", "session replay", "CRM/marketing", "tag manager")),
        "has_consent_platform": bool(out["consent_platforms"]),
        "has_ai_api": "AI API" in cats or "AI framework" in cats,
        "looks_ecommerce": out["signals"]["ecommerce_signals"]["count"] > 0 or any(c == "payments" for c in cats),
        "looks_ugc": out["signals"]["ugc_signals"]["count"] > 0,
        "collects_pii_in_forms": out["signals"]["pii_form_fields"]["count"] > 0,
        "missing_legal_pages": [k for k in ("legal_notice", "privacy_policy", "cookie_policy", "terms")
                                if out["legal_pages"][k]["count"] == 0],
        "possible_secrets": bool(out["secrets"]) or bool(env_files),
    }

    js = json.dumps(out, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(js)
        print(f"Scan written to {args.out}")
        print(json.dumps(out["summary"], indent=2, ensure_ascii=False))
    else:
        print(js)


if __name__ == "__main__":
    main()
