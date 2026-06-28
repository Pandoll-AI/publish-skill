import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"


def test_rewrite_does_not_add_unsolicited_sources_or_urls():
    text = "HBM은 AI 반도체에서 중요하다. 하지만 이 이유만으로 특정 주식을 지금 사야 한다고 단정할 수는 없다."
    with tempfile.TemporaryDirectory() as td:
        draft = Path(td) / "draft.md"
        draft.write_text(text, encoding="utf-8")
        out = Path(td) / "out"
        proc = subprocess.run(
            [sys.executable, str(ORCH), "--draft", str(draft), "--output", str(out), "--language", "ko"],
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, proc.stderr
        final = (out / "final_draft.md").read_text(encoding="utf-8")
        semantic_diff = json.loads((out / "semantic_diff.json").read_text(encoding="utf-8"))
        style_gate = json.loads((out / "style_gate.json").read_text(encoding="utf-8"))
        assert "http://" not in final
        assert "https://" not in final
        assert semantic_diff["source_added"] is False
        assert semantic_diff["added_sources"] == []
        assert style_gate["source_added"] is False
