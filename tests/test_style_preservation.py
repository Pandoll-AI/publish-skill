import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"


def test_style_pass_preserves_key_viewpoint_terms():
    text = "핵심은 기술 자체가 아니라 책임 구조다. 본 글은 중요한 시사점을 제공한다. 팀은 워크플로우를 먼저 정해야 한다."
    with tempfile.TemporaryDirectory() as td:
        draft = Path(td) / "draft.md"
        draft.write_text(text, encoding="utf-8")
        out = Path(td) / "out"
        proc = subprocess.run([sys.executable, str(ORCH), "--draft", str(draft), "--output", str(out), "--language", "ko"], text=True, capture_output=True)
        assert proc.returncode == 0, proc.stderr
        final = (out / "final_draft.md").read_text(encoding="utf-8")
        semantic_diff = json.loads((out / "semantic_diff.json").read_text(encoding="utf-8"))
        style_gate = json.loads((out / "style_gate.json").read_text(encoding="utf-8"))
        assert "책임 구조" in final
        assert "워크플로우" in final
        assert "중요한 시사점" not in final
        assert semantic_diff["semantic_drift"] is False
        assert style_gate["status"] in {"pass", "conditional_pass"}
