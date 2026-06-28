import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"
sys.path.insert(0, str(ROOT / "scripts"))

from orchestrate_publish import ALL_MODES  # noqa: E402
from validate_outputs import REQUIRED_FILES  # noqa: E402


def test_manifest_matches_runner_and_validator_contracts():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["version"] == "0.3.0"
    assert manifest["supported_modes"] == ALL_MODES
    assert manifest["outputs"] == REQUIRED_FILES


def test_verdict_scores_are_labelled_as_heuristic():
    with tempfile.TemporaryDirectory() as td:
        draft = Path(td) / "draft.md"
        draft.write_text("이 제품은 최근 팀의 문서 작성 시간을 30% 줄였다.", encoding="utf-8")
        out = Path(td) / "out"
        proc = subprocess.run(
            [sys.executable, str(ORCH), "--draft", str(draft), "--output", str(out), "--language", "ko"],
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, proc.stderr

        verdict = json.loads((out / "final_verdict.json").read_text(encoding="utf-8"))
        semantic_diff = json.loads((out / "semantic_diff.json").read_text(encoding="utf-8"))

        assert "scores" not in verdict
        assert verdict["score_basis"]["calibrated_quality_measure"] is False
        assert set(verdict["heuristic_scores"]) == {"factuality", "logic", "style", "readability", "traceability", "risk"}
        assert semantic_diff["method"] == "surface_claim_diff"
        assert semantic_diff["limits"]
