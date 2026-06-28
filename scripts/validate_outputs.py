#!/usr/bin/env python3
"""Validate a Publish Skill output directory using lightweight checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

REQUIRED_FILES = [
    "task_card.json",
    "claim_ledger.json",
    "fact_check_report.md",
    "evidence_registry.json",
    "argument_map.json",
    "logic_report.md",
    "logic_gate.json",
    "structure_plan.md",
    "style_profile.json",
    "style_pass.md",
    "semantic_diff.json",
    "style_gate.json",
    "line_edit.md",
    "risk_report.md",
    "change_log.md",
    "final_draft.md",
    "final_verdict.json",
]

VERDICT_STATUSES = {"pass", "conditional_pass", "revise_required", "fail"}
GATE_STATUSES = {"pass", "conditional_pass", "revise_required"}


def load_json(path: Path, errors: List[str]) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Invalid JSON {path.name}: {exc}")
        return {}


def validate_output_dir(output_dir: Path) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    for name in REQUIRED_FILES:
        path = output_dir / name
        if not path.exists():
            errors.append(f"Missing required artifact: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"Empty artifact: {name}")

    if not errors:
        task = load_json(output_dir / "task_card.json", errors)
        claims = load_json(output_dir / "claim_ledger.json", errors)
        registry = load_json(output_dir / "evidence_registry.json", errors)
        logic_gate = load_json(output_dir / "logic_gate.json", errors)
        semantic_diff = load_json(output_dir / "semantic_diff.json", errors)
        style_gate = load_json(output_dir / "style_gate.json", errors)
        verdict = load_json(output_dir / "final_verdict.json", errors)

        if task.get("language") not in {"ko", "en-GB", "mixed"}:
            errors.append("task_card.language must be ko, en-GB, or mixed")
        if not isinstance(claims.get("claims"), list):
            errors.append("claim_ledger.claims must be a list")
        if not isinstance(registry.get("entries"), list):
            errors.append("evidence_registry.entries must be a list")
        if claims.get("claims") and len(claims.get("claims", [])) != len(registry.get("entries", [])):
            errors.append("claim_ledger and evidence_registry entry counts differ")
        if verdict.get("status") not in VERDICT_STATUSES:
            errors.append("final_verdict.status is invalid")
        if logic_gate.get("status") not in GATE_STATUSES:
            errors.append("logic_gate.status is invalid")
        if style_gate.get("status") not in GATE_STATUSES:
            errors.append("style_gate.status is invalid")
        if not isinstance(semantic_diff.get("semantic_drift"), bool):
            errors.append("semantic_diff.semantic_drift must be boolean")
        if not isinstance(semantic_diff.get("source_added"), bool):
            errors.append("semantic_diff.source_added must be boolean")
        if semantic_diff.get("method") != "surface_claim_diff":
            errors.append("semantic_diff.method must be surface_claim_diff for the local scaffold")
        if not isinstance(semantic_diff.get("limits"), list) or not semantic_diff.get("limits"):
            errors.append("semantic_diff.limits must describe method limitations")
        if verdict.get("status") == "pass":
            if logic_gate.get("status") != "pass":
                errors.append("final_verdict cannot pass unless logic_gate.status is pass")
            if style_gate.get("status") != "pass":
                errors.append("final_verdict cannot pass unless style_gate.status is pass")
            if semantic_diff.get("semantic_drift"):
                errors.append("final_verdict cannot pass when semantic_drift is true")
            if semantic_diff.get("source_added"):
                errors.append("final_verdict cannot pass when source_added is true")
        scores = verdict.get("heuristic_scores", {})
        if not isinstance(scores, dict):
            errors.append("final_verdict.heuristic_scores must be an object")
            scores = {}
        score_basis = verdict.get("score_basis", {})
        if score_basis.get("calibrated_quality_measure") is not False:
            errors.append("final_verdict.score_basis must mark scores as non-calibrated heuristics")
        for key in ["factuality", "logic", "style", "readability", "traceability", "risk"]:
            val = scores.get(key)
            if not isinstance(val, (int, float)) or not (0 <= val <= 1):
                errors.append(f"final_verdict.heuristic_scores.{key} must be between 0 and 1")
        # No fake citation smoke check: unsupported entries must not carry evidence ids.
        for entry in registry.get("entries", []):
            if entry.get("support_status") in {"unsupported", "needs_current_check"} and entry.get("evidence_ids"):
                warnings.append(f"Entry {entry.get('claim_id')} has evidence IDs despite unsupported/current status; review manually.")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "required_files": REQUIRED_FILES}


def main(argv: List[str] | None = None) -> int:
    if not argv:
        argv = sys.argv[1:]
    if not argv:
        print("Usage: validate_outputs.py <output_dir>", file=sys.stderr)
        return 2
    result = validate_output_dir(Path(argv[0]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
