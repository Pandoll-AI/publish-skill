#!/usr/bin/env python3
"""Run Publish Skill on sample drafts."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / "scripts" / "orchestrate_publish.py"
SAMPLES = [
    ("korean_blog_draft.md", "ko", "blog article", "general professional readers"),
    ("english_linkedin_draft.md", "en-GB", "LinkedIn post", "technology leaders"),
]


def main() -> int:
    summaries = []
    for sample_name, language, purpose, audience in SAMPLES:
        draft = ROOT / "examples" / sample_name
        out = ROOT / "outputs" / f"sample_{draft.stem}"
        cmd = [
            sys.executable, str(ORCH),
            "--draft", str(draft),
            "--output", str(out),
            "--language", language,
            "--purpose", purpose,
            "--audience", audience,
            "--mode", "standard_publish",
            "--fact-check", "mixed",
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            return proc.returncode
        summaries.append(json.loads(proc.stdout))
    print(json.dumps({"ok": True, "runs": summaries}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
