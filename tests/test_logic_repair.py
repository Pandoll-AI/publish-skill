import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"


def test_logic_detects_overclaim_and_causal_leap():
    draft_text = "모든 회사는 AI 때문에 반드시 생산성이 오른다. 따라서 전통적인 팀은 사라질 것이다."
    with tempfile.TemporaryDirectory() as td:
        draft = Path(td) / "draft.md"
        draft.write_text(draft_text, encoding="utf-8")
        out = Path(td) / "out"
        proc = subprocess.run([sys.executable, str(ORCH), "--draft", str(draft), "--output", str(out), "--language", "ko"], text=True, capture_output=True)
        assert proc.returncode == 0, proc.stderr
        logic = json.loads((out / "logic_report.json").read_text(encoding="utf-8"))
        argument_map = json.loads((out / "argument_map.json").read_text(encoding="utf-8"))
        logic_gate = json.loads((out / "logic_gate.json").read_text(encoding="utf-8"))
        issue_types = {i["type"] for i in logic["issues"]}
        assert "overclaim" in issue_types
        assert "causal_leap" in issue_types
        assert argument_map["central_thesis"]
        assert logic_gate["status"] in {"conditional_pass", "revise_required"}
        assert logic_gate["required_repairs"]
