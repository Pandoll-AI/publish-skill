<h1 align="center">Publish Skill</h1>

<p align="center">
  <a href="README.md"><img alt="한국어로 보기" src="https://img.shields.io/badge/%ED%95%9C%EA%B5%AD%EC%96%B4%EB%A1%9C-%EB%B3%B4%EA%B8%B0-111827?style=for-the-badge"></a>
</p>

<p align="center">
  <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-skill-111827">
  <img alt="Version" src="https://img.shields.io/badge/version-0.3.0-0f766e">
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
  <img alt="Publish Skill poster hero" src="assets/hero.png">
</p>

<p align="center"><strong>Publish Skill is not a tool that polishes too early.</strong></p>

<p align="center">It separates claims first, marks evidence gaps and logic risks, and only then applies conservative edits where the draft can be made safer without inventing evidence.</p>

<p align="center"><strong>Current maturity: v0.3.0 scaffold.</strong> The local runner does not perform live web verification or deep semantic judgement.</p>

## Why It Exists

Most writing tools improve sentences before they inspect the reasoning. That can hide causal leaps, inflated claims, unsupported numbers, and generic AI phrasing inside smoother prose.

Publish Skill works in the opposite order.

```text
claims -> evidence gaps -> logic gate -> style pass -> surface claim diff -> final verdict
```

It is built for reports, columns, proposals, speeches, blog posts, LinkedIn posts, and any draft where visible verification gaps matter more than merely sounding polished.

## What It Does

- Heuristically separates fact, interpretation, opinion, prediction, and recommendation.
- Conservatively marks unsupported claims, current-state claims, and high-risk claims.
- Flags overclaiming, causal leaps, unsupported certainty, weak openings, and weak endings as a first-pass filter.
- Limits strong style rewriting when the logic gate blocks.
- Preserves authorial voice while reducing generic AI rhythm.
- Produces review artifacts including `claim_ledger`, `evidence_registry`, `logic_gate`, `style_gate`, and `final_verdict`.
- Does not invent sources, links, paper titles, statistics, organisations, or dates.

## What It Does Not Do

- The local runner does not browse the web.
- Codex agent execution may perform external verification as a separate step when the user requests it and tools are available.
- A URL in the draft is not treated as verified evidence.
- Supplied source metadata `supports` fields are recorded as user-provided signals; the local runner does not prove direct textual support.
- `semantic_diff.json` is a surface claim comparison, not an NLI or entailment judge.
- `final_verdict.json` exposes `heuristic_scores`; these are rule-based hints, not calibrated quality measurements.

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

Run the deterministic scaffold without network access. This is closer to claim audit and evidence-gap marking than full fact-checking.

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

See [examples/sample_output/korean_blog_draft](examples/sample_output/korean_blog_draft) for a real scaffold output set. It includes a `revise_required` verdict, showing how the local runner keeps evidence gaps visible.

## Modes

- `audit_only`: produce artifacts and gates without rewriting.
- `light_edit`: conservative edits while preserving the original structure.
- `quick_polish`: fast cleanup for low-risk text.
- `standard_publish`: default full final pass.
- `publish_gate`: strict publication decision.
- `strong_rewrite`: more aggressive restructuring while preserving verified meaning.
- `publish_ready`: legacy strict alias.
- `high_risk_review`: strict handling for medical, legal, financial, safety, or public-policy claims.
- `voice_rewrite`: preserve voice while improving force and rhythm.
- `explain_for_beginner`: explain a concept simply without adding unsupported facts.
- `fact_check_only`: review claims and evidence gaps without rewriting.
- `publication_style_only`: style-oriented artifacts only.
- `logic_only`: logic and structure review only.

## Principle

Publish Skill does not invent citations. If evidence is missing, it marks the claim as `source needed`, weakens the sentence, or removes it.

Style comes last. Facts and logic must pass first.

## Thanks

Publish Skill received deep inspiration from the Gongnyangi (@kimsh-1) user, and tries to implement a similar direction and sensibility.

Thank you to Gongnyangi for the standard and inspiration.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
