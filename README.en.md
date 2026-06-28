<h1 align="center">Publish Skill</h1>

<p align="center">
  <a href="README.md"><img alt="한국어로 보기" src="https://img.shields.io/badge/%ED%95%9C%EA%B5%AD%EC%96%B4%EB%A1%9C-%EB%B3%B4%EA%B8%B0-111827?style=for-the-badge"></a>
</p>

<p align="center">
  <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-skill-111827">
  <img alt="Skill validation" src="https://img.shields.io/badge/skill-valid-brightgreen">
  <img alt="Tests" src="https://img.shields.io/badge/tests-9%2F9-brightgreen">
  <img alt="Python" src="https://img.shields.io/badge/python-3.x-blue">
  <img alt="License" src="https://img.shields.io/github/license/Pandoll-AI/publish-skill">
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/Pandoll-AI/publish-skill">
  <img alt="Repo Size" src="https://img.shields.io/github/repo-size/Pandoll-AI/publish-skill">
  <img alt="Issues" src="https://img.shields.io/github/issues/Pandoll-AI/publish-skill">
  <img alt="Stars" src="https://img.shields.io/github/stars/Pandoll-AI/publish-skill?style=social">
  <img alt="Forks" src="https://img.shields.io/github/forks/Pandoll-AI/publish-skill?style=social">
  <img alt="Languages" src="https://img.shields.io/badge/language-ko%20%7C%20en--GB-0f766e">
  <img alt="No Invented Citations" src="https://img.shields.io/badge/source%20policy-no%20invented%20citations-f59e0b">
</p>

<p align="center">
  <img alt="Publish Skill hero" src="assets/hero.svg">
</p>

<p align="center"><strong>Publish Skill is not a tool that polishes too early.</strong></p>

<p align="center">It separates facts first, weakens unsupported certainty, repairs gaps in the argument, and only then turns the draft into publication-ready prose with the author's voice intact.</p>

## Why It Exists

Most writing tools improve sentences before they inspect the reasoning. That can hide causal leaps, inflated claims, unsupported numbers, and generic AI phrasing inside smoother prose.

Publish Skill works in the opposite order.

```text
claims -> evidence -> logic gate -> style pass -> semantic diff -> final verdict
```

It is built for reports, columns, proposals, speeches, blog posts, LinkedIn posts, and any draft where being publishable matters more than merely sounding polished.

## What It Does

- Separates fact, interpretation, opinion, prediction, and recommendation.
- Flags overclaiming, causal leaps, unsupported certainty, weak openings, and weak endings.
- Applies a logic gate before strong style rewriting.
- Preserves authorial voice while reducing generic AI rhythm.
- Produces `final_draft`, `change_log`, `evidence_registry`, `logic_gate`, `style_gate`, and `final_verdict`.
- Does not invent sources, links, paper titles, statistics, organisations, or dates.

## Install

Clone the repo into your Codex skills directory.

```bash
git clone https://github.com/Pandoll-AI/publish-skill.git ~/.codex/skills/publish-skill
```

Or symlink an existing checkout.

```bash
ln -s /path/to/publish-skill ~/.codex/skills/publish-skill
```

Then ask Codex:

```text
Use $publish-skill to polish this draft for publication with fact, logic, and style checks.
```

## Local Scaffold

Run the deterministic scaffold without network access.

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

Run the tests:

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

## Principle

Publish Skill does not invent citations. If evidence is missing, it marks the claim as `source needed`, weakens the sentence, or removes it.

Style comes last. Facts and logic must pass first.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
