"""Behaviour of scripts/scan_project.py through its CLI, the interface SKILL.md tells agents to use."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCANNER = Path(__file__).resolve().parents[1] / "skills/eu-legal-compliance-audit/scripts/scan_project.py"


def write(root, rel, content):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def scan(root, *args):
    result = subprocess.run(
        [sys.executable, "-I", str(SCANNER), str(root), *args],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def services(report):
    return {s["service"]: s for s in report["third_party_services"]}


def test_trackers_without_consent_platform_are_reported_with_location_and_vendor(tmp_path):
    write(tmp_path, "src/layouts/Default.html", """<html lang="es"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC1234567"></script>
<script>fbq('init', '123');</script>
</head></html>
""")

    report = scan(tmp_path)

    found = services(report)
    assert found["Google Analytics"]["usual_vendor_location"] == "US"
    assert found["Google Analytics"]["consent_needed_default"] == "yes"
    assert found["Google Analytics"]["evidence"][0].startswith("src/layouts/Default.html:2:")
    assert "Meta Pixel" in found
    assert report["summary"]["has_tracking_services"] is True
    assert report["summary"]["has_consent_platform"] is False


def test_consent_platform_is_detected(tmp_path):
    write(tmp_path, "index.html",
          '<script id="Cookiebot" src="https://consent.cookiebot.com/uc.js"></script>\n')

    report = scan(tmp_path)

    assert "Cookiebot" in report["consent_platforms"]
    assert report["summary"]["has_consent_platform"] is True


def test_cookieless_analytics_alone_is_not_tracking(tmp_path):
    write(tmp_path, "index.html", '<script defer src="https://plausible.io/js/script.js"></script>\n')

    report = scan(tmp_path)

    assert services(report)["Plausible"]["consent_needed_default"] == "no"
    assert report["summary"]["has_tracking_services"] is False


def test_missing_legal_pages_lists_only_absent_ones(tmp_path):
    write(tmp_path, "pages/aviso-legal.vue", "<template><h1>Aviso legal</h1></template>\n")
    write(tmp_path, "app/privacy-policy/page.tsx", "export default function Page() { return null }\n")

    report = scan(tmp_path)

    assert report["summary"]["missing_legal_pages"] == ["cookie_policy", "terms"]


def test_readme_todo_about_legal_pages_does_not_hide_their_absence(tmp_path):
    write(tmp_path, "README.md", "TODO: write the privacy policy, terms of service and aviso legal\n")
    write(tmp_path, "index.html", '<html lang="en"><body>Shop</body></html>\n')

    report = scan(tmp_path)

    assert report["summary"]["missing_legal_pages"] == [
        "legal_notice", "privacy_policy", "cookie_policy", "terms",
    ]


def test_documentation_mentioning_services_does_not_count_as_usage(tmp_path):
    write(tmp_path, "docs/integrations.md", "We considered Google Analytics (gtag('config')) and Hotjar.\n")

    report = scan(tmp_path)

    assert report["third_party_services"] == []


def test_build_and_dependency_folders_are_ignored(tmp_path):
    tracker = "<script src=\"https://connect.facebook.net/en_US/fbevents.js\"></script>\n"
    write(tmp_path, "dist/index.html", tracker)
    write(tmp_path, "node_modules/lib/index.js", tracker)

    report = scan(tmp_path)

    assert report["third_party_services"] == []


def test_preticked_marketing_consent_is_flagged_but_unticked_is_not(tmp_path):
    write(tmp_path, "signup.html", """<form>
<label><input type="checkbox" name="newsletter" checked> Quiero recibir ofertas comerciales</label>
</form>
""")
    write(tmp_path, "contact.html", """<form>
<label><input type="checkbox" name="newsletter"> Quiero recibir ofertas comerciales</label>
</form>
""")
    write(tmp_path, "settings.html", '<input type="checkbox" name="dark_mode" checked> Dark mode\n')

    signal = scan(tmp_path)["signals"]["preticked_consent_checkbox"]

    assert signal["count"] == 1
    assert signal["evidence"][0].startswith("signup.html:2:")


def test_preticked_box_is_judged_by_its_own_label_not_its_neighbours(tmp_path):
    write(tmp_path, "login.html", """<label>
<input type="checkbox" name="newsletter">
Quiero recibir ofertas</label>
<input type="checkbox" name="remember" checked> Remember me
""")

    assert scan(tmp_path)["signals"]["preticked_consent_checkbox"]["count"] == 0


def test_preticked_box_labelled_by_for_attribute_is_flagged(tmp_path):
    write(tmp_path, "signup.html", """<label for="opt">Acepto recibir publicidad</label>
<input type="checkbox" id="opt" checked>
""")

    evidence = scan(tmp_path)["signals"]["preticked_consent_checkbox"]["evidence"]

    assert [e.split(":")[:2] for e in evidence] == [["signup.html", "2"]]


def test_label_for_a_similar_id_does_not_label_the_checkbox(tmp_path):
    write(tmp_path, "login.html", """<label for="opt-in">Acepto recibir publicidad</label>
<input type="checkbox" id="opt" checked> Recordarme
""")

    assert scan(tmp_path)["signals"]["preticked_consent_checkbox"]["count"] == 0


def test_preticked_multiline_jsx_checkbox_is_flagged(tmp_path):
    write(tmp_path, "Signup.tsx", """export const Signup = () => (
  <input
    type="checkbox"
    name="marketing"
    defaultChecked={true}
  />
);
""")

    evidence = scan(tmp_path)["signals"]["preticked_consent_checkbox"]["evidence"]

    assert [e.split(":")[:2] for e in evidence] == [["Signup.tsx", "5"]]


def git_repo(root):
    subprocess.run(["git", "init", "-q", str(root)], check=True)


def test_gitignored_env_and_secrets_are_not_reported_as_committed(tmp_path):
    git_repo(tmp_path)
    write(tmp_path, ".gitignore", ".env\n")
    write(tmp_path, ".env", "AWS_KEY=AKIA" + "ABCDEFGHIJKLMNOP\n")

    report = scan(tmp_path)

    assert not any("Not a git repository" in n for n in report["notes"])
    assert report["committed_env_files"] == []
    assert report["secrets"] == {}
    assert report["summary"]["possible_secrets"] is False


def test_env_not_ignored_in_git_repo_is_reported_even_before_commit(tmp_path):
    git_repo(tmp_path)
    write(tmp_path, ".env", "AWS_KEY=AKIA" + "ABCDEFGHIJKLMNOP\n")

    report = scan(tmp_path)

    assert report["committed_env_files"] == [".env"]
    assert "AWS access key" in report["secrets"]


def test_secrets_are_reported_without_leaking_the_value(tmp_path):
    key = "AKIA" + "ABCDEFGHIJKLMNOP"
    write(tmp_path, "config.js", f"const awsKey = '{key}';\n")

    report = scan(tmp_path)

    evidence = report["secrets"]["AWS access key"]["evidence"]
    assert evidence == ["config.js:1: <redacted match> config.js"]
    assert key not in json.dumps(report)
    assert report["summary"]["possible_secrets"] is True


def test_placeholder_secrets_are_ignored(tmp_path):
    write(tmp_path, "config.js", "const awsKey = 'AKIAABCDEFGHIJKLMNOP'; // example value\n")

    assert scan(tmp_path)["secrets"] == {}


def test_env_files_are_listed_but_templates_are_not(tmp_path):
    write(tmp_path, ".env", "DATABASE_URL=postgres://localhost/app\n")
    write(tmp_path, ".env.example", "DATABASE_URL=\n")

    report = scan(tmp_path)

    assert report["committed_env_files"] == [".env"]
    assert any("Not a git repository" in n for n in report["notes"])


@pytest.mark.parametrize("license_value, flagged", [
    ("AGPL-3.0-only", True),
    ("(GPL-2.0 OR GPL-3.0)", True),
    ("GPL-2.0 AND MIT", True),
    ("MIT", False),
    ("MIT OR GPL-3.0", False),
    ("(GPL-3.0 OR Apache-2.0)", False),
])
def test_copyleft_dependencies(tmp_path, license_value, flagged):
    write(tmp_path, "node_modules/pkg/package.json",
          json.dumps({"name": "pkg", "version": "1.0.0", "license": license_value}))

    copyleft = scan(tmp_path)["licenses"]["copyleft"]

    assert [p["package"] for p in copyleft] == (["pkg"] if flagged else [])


def test_accessibility_signals(tmp_path):
    write(tmp_path, "bad.html", '<html><body><img src="logo.png"></body></html>\n')
    write(tmp_path, "good.html", '<html lang="es"><body><img src="logo.png" alt="Logo"></body></html>\n')

    a11y = scan(tmp_path)["accessibility"]

    assert a11y["html_without_lang"]["evidence"] == ["bad.html:1: <html><body><img src=\"logo.png\"></body></html>"]
    assert [e.split(":")[0] for e in a11y["img_without_alt"]["evidence"]] == ["bad.html"]


def test_ai_sdk_and_ecommerce_profile_gates(tmp_path):
    write(tmp_path, "server/chat.ts", "import OpenAI from 'openai';\n")
    write(tmp_path, "server/pay.ts", "import Stripe from 'stripe';\n")

    summary = scan(tmp_path)["summary"]

    assert summary["has_ai_api"] is True
    assert summary["looks_ecommerce"] is True


def test_empty_static_site_has_no_false_alarms(tmp_path):
    write(tmp_path, "index.html", '<html lang="en"><body><h1>Portfolio</h1></body></html>\n')

    summary = scan(tmp_path)["summary"]

    assert summary["has_tracking_services"] is False
    assert summary["has_ai_api"] is False
    assert summary["looks_ecommerce"] is False
    assert summary["collects_pii_in_forms"] is False
    assert summary["possible_secrets"] is False


def test_max_evidence_caps_evidence_but_not_count(tmp_path):
    write(tmp_path, "a.js", "localStorage.setItem('a', 1)\n" * 5)

    writes = scan(tmp_path, "--max-evidence", "2")["signals"]["storage_writes"]

    assert writes["count"] == 5
    assert len(writes["evidence"]) == 2


def test_out_file_contains_full_report_and_stdout_the_summary(tmp_path):
    project = tmp_path / "project"
    write(project, "index.html", '<html lang="en"></html>\n')
    out = tmp_path / "scan.json"

    result = subprocess.run([sys.executable, "-I", str(SCANNER), str(project), "--out", str(out)],
                            capture_output=True, text=True, check=True)

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["root"] == str(project)
    assert report["files_scanned"] == 1
    assert '"missing_legal_pages"' in result.stdout


def test_non_directory_root_fails(tmp_path):
    result = subprocess.run([sys.executable, "-I", str(SCANNER), str(tmp_path / "missing")],
                            capture_output=True, text=True)

    assert result.returncode != 0
    assert "Not a directory" in result.stderr
