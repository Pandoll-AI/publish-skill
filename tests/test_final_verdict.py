import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"


def test_high_risk_unverified_claim_requires_revision():
    text = "현재 이 투자 전략은 수익률을 30% 높인다. 모든 투자자는 이 전략을 반드시 따라야 한다."
    with tempfile.TemporaryDirectory() as td:
        draft = Path(td) / "draft.md"
        draft.write_text(text, encoding="utf-8")
        out = Path(td) / "out"
        proc = subprocess.run([sys.executable, str(ORCH), "--draft", str(draft), "--output", str(out), "--language", "ko", "--mode", "publish_ready"], text=True, capture_output=True)
        assert proc.returncode == 0, proc.stderr
        verdict = json.loads((out / "final_verdict.json").read_text(encoding="utf-8"))
        assert verdict["status"] in {"revise_required", "fail"}
        assert verdict["blocking_issues"]
