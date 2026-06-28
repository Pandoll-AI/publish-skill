# Publish Skill

![Codex Skill](https://img.shields.io/badge/Codex-skill-111827)
![Skill validation](https://img.shields.io/badge/skill-valid-brightgreen)
![Tests](https://img.shields.io/badge/tests-9%2F9-brightgreen)
![Python](https://img.shields.io/badge/python-3.x-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

![Publish Skill hero](assets/hero.png)

Publish Skill is a fact-first final editor for serious drafts. It turns rough prose into publication-ready writing by checking claims before style, repairing weak logic before polish, and preserving the author's voice without inventing evidence.

Use it when a draft is almost important enough to publish, but not yet trustworthy enough to ship.

## What It Does

- Mines factual claims and separates fact, interpretation, opinion, prediction, and recommendation.
- Flags overclaiming, causal leaps, unsupported certainty, weak openings, and weak endings.
- Applies a logic gate before style rewriting, so elegant prose does not hide broken reasoning.
- Preserves authorial voice while removing generic AI rhythm and inflated phrasing.
- Produces a final draft, change log, evidence registry, logic report, style gate, and verdict.

## Why It Feels Different

Most writing tools polish sentences too early. Publish Skill treats publication as a sequence of gates:

```text
claims -> evidence -> argument map -> logic gate -> style pass -> semantic diff -> final verdict
```

That makes it useful for essays, columns, memos, speeches, proposals, reports, blog posts, LinkedIn posts, and any draft where sounding good is not enough.

## Install

Clone the repo into your Codex skills directory:

```bash
git clone https://github.com/Pandoll-AI/publish-skill.git ~/.codex/skills/publish-skill
```

Or symlink an existing checkout:

```bash
ln -s /path/to/publish-skill ~/.codex/skills/publish-skill
```

Then ask Codex:

```text
Use $publish-skill to polish this draft for publication with fact, logic, and style checks.
```

## Local Scaffold

Run the deterministic scaffold without network access:

```bash
python3 scripts/orchestrate_publish.py \
  --draft examples/english_linkedin_draft.md \
  --output outputs/example_run \
  --language en-GB \
  --mode standard_publish \
  --fact-check mixed
```

Validate the output set:

```bash
python3 scripts/validate_outputs.py outputs/example_run
```

Run the test suite:

```bash
python3 tests/run_tests.py
```

## Modes

- `quick_polish`: fast cleanup for low-risk text.
- `standard_publish`: default full final pass.
- `publish_gate`: strict publication decision.
- `high_risk_review`: strict handling for medical, legal, financial, safety, or public-policy claims.
- `voice_rewrite`: preserve voice while improving force and rhythm.
- `explain_for_beginner`: explain a concept simply without adding unsupported facts.

## Source Discipline

Publish Skill does not invent citations, links, statistics, papers, organisations, names, or dates. If source work was not requested or supplied, it marks unsupported claims as `source needed`, weakens them, or removes them.

## License

MIT
