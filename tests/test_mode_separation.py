import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"


def run_mode(text: str, mode: str, language: str = "ko"):
    with tempfile.TemporaryDirectory() as td:
        draft = Path(td) / "draft.md"
        draft.write_text(text, encoding="utf-8")
        out = Path(td) / "out"
        proc = subprocess.run(
            [sys.executable, str(ORCH), "--draft", str(draft), "--output", str(out), "--language", language, "--mode", mode],
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, proc.stderr
        return {
            "final": (out / "final_draft.md").read_text(encoding="utf-8"),
            "verdict": json.loads((out / "final_verdict.json").read_text(encoding="utf-8")),
            "logic_gate": json.loads((out / "logic_gate.json").read_text(encoding="utf-8")),
            "style_gate": json.loads((out / "style_gate.json").read_text(encoding="utf-8")),
        }


def test_quick_polish_allows_safe_rewrite_but_publish_gate_blocks():
    text = "모든 회사는 AI 때문에 반드시 생산성이 오른다. 따라서 전통적인 팀은 사라질 것이다."
    quick = run_mode(text, "quick_polish")
    strict = run_mode(text, "publish_gate")

    assert quick["logic_gate"]["status"] == "revise_required"
    assert quick["verdict"]["status"] == "conditional_pass"
    assert "많은 회사" in quick["final"] or "상황에 따라" in quick["final"]

    assert strict["logic_gate"]["status"] == "revise_required"
    assert strict["verdict"]["status"] == "revise_required"
    assert strict["style_gate"]["status"] == "revise_required"


def test_high_risk_review_blocks_unsupported_financial_claims():
    text = "이 전략은 모든 투자자의 수익률을 30% 높인다. 따라서 투자자는 전문가 검토 없이 전 재산을 넣어야 한다."
    result = run_mode(text, "high_risk_review")

    assert result["verdict"]["status"] == "revise_required"
    assert result["logic_gate"]["blockers"]
    assert result["style_gate"]["status"] == "revise_required"
