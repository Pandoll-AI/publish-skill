#!/usr/bin/env python3
"""Audit the Publish Skill package structure and smoke-test execution."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from orchestrate_publish import ALL_MODES  # noqa: E402
from validate_outputs import REQUIRED_FILES  # noqa: E402

REQUIRED_PATHS = [
    "SKILL.md",
    "manifest.json",
    "agents/openai.yaml",
    "configs/publication_style_ko.yaml",
    "configs/publication_style_en_gb.yaml",
    "configs/fact_check_policy.yaml",
    "configs/risk_rules.yaml",
    "configs/edit_modes.yaml",
    "scripts/orchestrate_publish.py",
    "scripts/extract_claims.py",
    "scripts/validate_outputs.py",
    "scripts/run_sample.py",
    "schemas/argument_map.schema.json",
    "schemas/task_card.schema.json",
    "schemas/claim_ledger.schema.json",
    "schemas/evidence_registry.schema.json",
    "schemas/logic_gate.schema.json",
    "schemas/semantic_diff.schema.json",
    "schemas/style_gate.schema.json",
    "schemas/final_verdict.schema.json",
]
OLD_SPECIALISED_TERMS = [
    "render_pdf_pages.py",
    "Typst/LaTeX/Quarto/Paged.js template inspection",
    "AI/LLM-history-specific evidence registry",
]
OLD_NAME_PATTERNS = [
    re.compile(r"\b" + "Le" + "e" + r"\b"),
    re.compile("le" + "e" + r"[-_ ]style", re.IGNORECASE),
    re.compile("le" + "e" + r"[-_ ]finali[sz]er", re.IGNORECASE),
    re.compile("le" + "e" + "_final" + "iser", re.IGNORECASE),
    re.compile("07_" + "le" + "e" + "_style_agent", re.IGNORECASE),
    re.compile("orchestrate_" + "final" + "ise" + r"\.py", re.IGNORECASE),
]


def read_json(path: Path, errors: List[str]) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")
        return {}


def audit(run_smoke: bool = True) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    for rel in REQUIRED_PATHS:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"Missing required file: {rel}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"Empty required file: {rel}")

    prompts = sorted((ROOT / "prompts").glob("*.md"))
    if len(prompts) != 11:
        errors.append(f"Expected 11 prompts; found {len(prompts)}")
    for p in prompts:
        text = p.read_text(encoding="utf-8")
        for phrase in ["bounded input", "artifact", "verdict", "terminate"]:
            if phrase.lower() not in text.lower():
                errors.append(f"Prompt {p.name} lacks lifecycle phrase: {phrase}")

    manifest = read_json(ROOT / "manifest.json", errors)
    if manifest.get("name") != "publish-skill":
        errors.append("manifest.name must be publish-skill")
    if manifest.get("version") != "0.3.0":
        errors.append("manifest.version must reflect current scaffold maturity: 0.3.0")
    if "PDF" in manifest.get("description", ""):
        errors.append("manifest description still appears layout/PDF-specific")
    if "fact-checks claims" in manifest.get("description", "").lower():
        errors.append("manifest description overstates local factual verification")
    if "topic" not in manifest.get("description", "").lower() and "agnostic" not in manifest.get("description", "").lower():
        warnings.append("Manifest description should emphasise topic-agnostic behaviour")
    if manifest.get("supported_modes") != ALL_MODES:
        errors.append("manifest.supported_modes must match scripts.orchestrate_publish.ALL_MODES")
    if manifest.get("outputs") != REQUIRED_FILES:
        errors.append("manifest.outputs must match scripts.validate_outputs.REQUIRED_FILES")

    readme_text = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    readme_en_text = (ROOT / "README.en.md").read_text(encoding="utf-8") if (ROOT / "README.en.md").exists() else ""
    for name, text in [("README.md", readme_text), ("README.en.md", readme_en_text)]:
        if "tests-9%2F9" in text or "skill-valid" in text:
            errors.append(f"{name} uses a static validation/test badge")

    combined_core = "\n".join(
        (ROOT / rel).read_text(encoding="utf-8")
        for rel in ["SKILL.md", "manifest.json", "agents/openai.yaml"]
        if (ROOT / rel).exists()
    )
    for term in OLD_SPECIALISED_TERMS:
        if term in combined_core and "Removed" not in combined_core:
            errors.append(f"Old specialised term remains in core as active feature: {term}")

    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(part in {".git", "outputs", "dist"} for part in path.relative_to(ROOT).parts):
            continue
        for pattern in OLD_NAME_PATTERNS:
            if pattern.search(rel):
                errors.append(f"Old name dependency remains in path: {rel}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in OLD_NAME_PATTERNS:
            if pattern.search(text):
                errors.append(f"Old name dependency remains in {rel}: {pattern.pattern}")

    # Syntax compile scripts and tests.
    for py in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "tests").glob("*.py")):
        proc = subprocess.run([sys.executable, "-m", "py_compile", str(py)], capture_output=True, text=True)
        if proc.returncode != 0:
            errors.append(f"Python compile failed for {py.relative_to(ROOT)}: {proc.stderr.strip()}")

    smoke_summary: Dict[str, Any] | None = None
    if run_smoke and not errors:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "sample_out"
            proc = subprocess.run([
                sys.executable, str(ROOT / "scripts" / "orchestrate_publish.py"),
                "--draft", str(ROOT / "examples" / "korean_blog_draft.md"),
                "--output", str(out),
                "--language", "ko",
                "--purpose", "blog article",
                "--audience", "general professional readers",
                "--mode", "standard_publish",
                "--fact-check", "mixed",
            ], capture_output=True, text=True)
            if proc.returncode != 0:
                errors.append(f"Smoke orchestrator failed: {proc.stderr.strip() or proc.stdout.strip()}")
            else:
                smoke_summary = json.loads(proc.stdout)
                val = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_outputs.py"), str(out)], capture_output=True, text=True)
                if val.returncode != 0:
                    errors.append(f"Smoke validation failed: {val.stdout.strip()} {val.stderr.strip()}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "prompt_count": len(prompts),
        "smoke_summary": smoke_summary,
    }


def main() -> int:
    result = audit(run_smoke=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
