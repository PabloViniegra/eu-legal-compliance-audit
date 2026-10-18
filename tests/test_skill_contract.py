"""Structural guarantees of the skill: valid Agent Skills metadata and internally consistent references."""
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / "skills/eu-legal-compliance-audit"
SKILL_MD = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
CONTROLS = (SKILL_DIR / "references/controls.md").read_text(encoding="utf-8")
FINES_ES = (SKILL_DIR / "references/fines-spain.md").read_text(encoding="utf-8")
TEMPLATE = (SKILL_DIR / "references/report-template.md").read_text(encoding="utf-8")


def frontmatter():
    match = re.match(r"^---\n(.*?)\n---\n", SKILL_MD, re.S)
    assert match, "SKILL.md must start with YAML frontmatter"
    return dict(re.findall(r"^([a-z_-]+):\s*(.*)$", match.group(1), re.M))


def test_frontmatter_follows_agent_skills_spec():
    meta = frontmatter()

    assert meta["name"] == SKILL_DIR.name
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", meta["name"])
    assert len(meta["name"]) <= 64
    assert 0 < len(meta["description"]) <= 1024
    assert "<" not in meta["description"] and ">" not in meta["description"]


def test_skill_body_stays_within_recommended_size():
    assert len(SKILL_MD.splitlines()) < 500


def test_every_bundled_file_mentioned_in_skill_md_exists():
    mentioned = set(re.findall(r"(?:references|scripts)/[\w.-]+\.(?:md|py)", SKILL_MD))

    assert mentioned, "SKILL.md should point to its references and scripts"
    assert sorted(p for p in mentioned if not (SKILL_DIR / p).is_file()) == []


def test_every_reference_file_is_reachable_from_skill_md():
    bundled = {f"references/{p.name}" for p in (SKILL_DIR / "references").glob("*.md")}

    assert sorted(p for p in bundled if p not in SKILL_MD) == []


def test_every_infraction_key_in_controls_has_a_spanish_fine_row():
    keys = set()
    for line in CONTROLS.splitlines():
        if "Infraction key" in line:
            keys.update(re.findall(r"`([A-Z][A-Z0-9.-]+)`", line))
    priced = set(re.findall(r"^\| `([A-Z][A-Z0-9.-]+)` \|", FINES_ES, re.M))

    assert keys, "controls.md should declare infraction keys"
    assert sorted(keys - priced) == []


def test_control_ids_used_in_report_template_exist():
    defined = set(re.findall(r"^### ([A-Z]+-\d+)\b", CONTROLS, re.M))
    defined |= set(re.findall(r"^\| ([A-Z]+-\d+) \|", CONTROLS, re.M))
    used = set(re.findall(r"\b([A-Z]{2,4}-\d{2})\b", TEMPLATE))

    assert sorted(used - defined) == []


def test_statuses_in_skill_md_are_translated_in_report_template():
    statuses = re.findall(r"^- \*\*([A-Z/]+)\*\* —", SKILL_MD, re.M)

    assert statuses == ["FAIL", "PARTIAL", "PASS", "MANUAL", "N/A"]
    for status in ("FAIL", "PARTIAL", "PASS", "MANUAL"):
        assert re.search(rf"\b{status} →", TEMPLATE), status


def test_time_sensitive_references_carry_a_verification_date():
    for name in ("controls.md", "fines-spain.md", "fines-eu.md"):
        text = (SKILL_DIR / "references" / name).read_text(encoding="utf-8")
        assert re.search(r"^Last verified: \d{4}-\d{2}-\d{2}\.", text, re.M), name


def test_scanner_command_documented_in_skill_md_runs(tmp_path):
    command = re.search(r"python3 <skill-dir>/(scripts/\S+) <project-root> --out (\S+)", SKILL_MD)
    assert command, "SKILL.md should document how to run the scanner"
    (tmp_path / "index.html").write_text('<html lang="en"></html>\n', encoding="utf-8")
    out = tmp_path / "scan.json"

    subprocess.run([sys.executable, "-I", str(SKILL_DIR / command.group(1)), str(tmp_path), "--out", str(out)],
                   check=True, capture_output=True)

    assert out.is_file()
