import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"
EXAMPLES = [
    "korean_blog_draft.md",
    "english_linkedin_draft.md",
    "ai_strategy_memo.md",
    "product_launch_note.md",
    "business_proposal_excerpt.md",
]


def run_example(name: str):
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "out"
        cmd = [
            sys.executable, str(ORCH),
            "--draft", str(ROOT / "examples" / name),
            "--output", str(out),
            "--mode", "standard_publish",
            "--fact-check", "mixed",
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        assert proc.returncode == 0, proc.stderr
        summary = json.loads(proc.stdout)
        verdict = json.loads((out / "final_verdict.json").read_text(encoding="utf-8"))
        return summary, verdict


def test_runs_across_unrelated_topics():
    statuses = []
    for example in EXAMPLES:
        summary, verdict = run_example(example)
        assert summary["ok"] is True
        assert verdict["status"] in {"pass", "conditional_pass", "revise_required", "fail"}
        statuses.append(verdict["status"])
    assert len(statuses) == len(EXAMPLES)
