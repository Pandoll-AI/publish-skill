import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"


def test_unsupported_claims_do_not_get_fake_evidence_ids():
    with tempfile.TemporaryDirectory() as td:
        draft = Path(td) / "draft.md"
        draft.write_text("현재 AlphaProduct는 시장 점유율 80%를 차지한다. 모든 기업은 반드시 도입해야 한다.", encoding="utf-8")
        out = Path(td) / "out"
        proc = subprocess.run([sys.executable, str(ORCH), "--draft", str(draft), "--output", str(out), "--language", "ko"], text=True, capture_output=True)
        assert proc.returncode == 0, proc.stderr
        registry = json.loads((out / "evidence_registry.json").read_text(encoding="utf-8"))
        for entry in registry["entries"]:
            if entry["support_status"] in {"unsupported", "needs_current_check"}:
                assert entry["evidence_ids"] == []
                assert entry["source_summary"] == ""
