---
name: publish-skill
description: Fact-first publication workflow scaffold for drafts, memos, articles, speeches, emails, proposals, essays, reports, LinkedIn posts, blog posts, columns, and other prose. Use when the user asks to prepare text for publication, audit claims and evidence gaps, improve logic, reduce AI tone, preserve authorial voice, or produce a final draft with change notes and a conservative verdict. Full factual verification requires supplied sources or an explicit external research workflow.
---

# Publish Skill

## Mission

Guide a draft toward a safer publication version by doing the work in this order:

1. Identify the task, language, audience, purpose, mode, and risk level.
2. Mine factual claims and separate facts, interpretations, opinions, predictions, and recommendations.
3. Check which claims require evidence and whether any supplied evidence supports them.
4. Repair logical flow, over-claims, missing assumptions, causal leaps, contradictions, and weak conclusions.
5. Improve structure and paragraph order.
6. Apply publication style without changing the verified meaning.
7. Line-edit for human rhythm, clarity, sentence length, repetition, and AI-sounding phrases.
8. Review bias, hype, and risk.
9. Produce a final draft, change log, and final verdict.

This skill is a workflow scaffold. The bundled local runner is deterministic and heuristic: it records claims, supplied evidence, evidence gaps, logic risks, style risks, and conservative edits. It does not perform live web verification, source-content entailment, or deep semantic judgement by itself.

## Non-Negotiable Rules

- Facts before style. Do not make a sentence more elegant before checking whether its factual force is safe.
- Never invent citations, URLs, paper titles, statistics, organisations, names, or dates.
- Do not add external citations, URLs, or source names unless the user explicitly asks for research/source checking or supplies source metadata. Mark `source needed` instead.
- Do not strengthen claims unless evidence is present.
- If a claim cannot be verified, mark it, weaken it, or remove it.
- Preserve the user's core argument and point of view unless it is factually unsafe or logically broken.
- Keep the final result topic-agnostic. Do not assume the text is about AI, medicine, investment, business, or any other domain unless the draft says so.
- In Korean, prefer clear, calm, decisive prose with short paragraphs and minimal AI-style abstraction.
- In English, prefer British English and avoid US-style hype.
- For medical, legal, financial, safety, or public-policy claims, raise the evidential threshold.

## Bundled Workflow

- Use `prompts/` for the multi-agent publication workflow when the task needs staged review.
- Use `configs/` for mode, risk, fact-check, and publication-style policy.
- Use `schemas/` to validate structured artifacts when writing or reviewing outputs.
- Use `scripts/orchestrate_publish.py` for a deterministic local scaffold that creates the artifact set without network access. Treat it as claim/evidence-gap marking plus conservative editing, not full factual verification.
- Use `scripts/validate_outputs.py` to check an output directory.
- Use `scripts/package_audit.py` before distributing the skill package.

## Quality Gate Loop

Use at most one retry for each gate. Do not proceed to publication-style rewriting while the logic gate has blocking issues.

```text
claim_ledger
-> evidence_registry
-> argument_map
-> logic_critic
-> logic_repair_plan
-> logic_gate
-> style_profile
-> style_candidate
-> semantic_diff
-> style_gate
-> final_architect
```

The final architect must not return `pass` unless:

- `logic_gate.json.status` is `pass`;
- `style_gate.json.status` is `pass`;
- `semantic_diff.json.semantic_drift` is `false`;
- unresolved evidence gaps are either weakened, removed, or explicitly marked.

## Mode Selection

Choose the lightest mode that fits the request:

- `audit_only`: Produce artifacts and gate findings without rewriting the draft.
- `light_edit`: Apply conservative edits while preserving the original structure.
- `quick_polish`: Short low-risk text cleanup. Use gate thinking internally, but keep the user-facing output concise. Do not add sources.
- `standard_publish`: Default full final pass for ordinary publication work.
- `publish_gate`: Strict publication decision. Block final `pass` unless logic, style, semantic, source, and evidence gates pass.
- `strong_rewrite`: Allow more aggressive restructuring while preserving verified meaning.
- `publish_ready`: Legacy strict alias for publish-gate style behaviour.
- `high_risk_review`: Medical, legal, financial, safety, or public-policy prose. Block on any unsupported high-risk claim.
- `voice_rewrite`: Preserve authorial voice while improving rhythm, clarity, and force. Do not overwrite the author's point of view.
- `explain_for_beginner`: Explain a concept simply with accurate analogies and explicit limits. Do not add unsupported examples or sources.
- `fact_check_only`: Mine claims and evidence gaps without rewriting.
- `publication_style_only`: Run style-oriented artifacts only after respecting source policy.
- `logic_only`: Focus on argument map, logic report, and structure plan without rewriting.

For `quick_polish`, `voice_rewrite`, and `explain_for_beginner`, unresolved non-high-risk logic issues may produce `conditional_pass` rather than blocking all rewriting. High-risk blockers still prevent publication-ready style polishing.

## Source Policy

Default to no new external sources. Use only sources already present in the draft, supplied by the user, or explicitly requested by the user.

When a claim needs evidence but source work was not requested:

- mark the claim as `source needed`;
- weaken or caveat the sentence;
- do not add a citation, URL, paper title, institution, or source name from memory.

When source work is explicitly requested:

- separate checked sources from unverified source candidates;
- record any added source in `semantic_diff.json`;
- do not let the final verdict return `pass` if a source was added but not clearly checked.

## Agent Lifecycle Contract

Each sub-agent must follow:

```text
spawn -> bounded input read -> artifact write -> verdict JSON -> terminate
```

Each agent receives only the bounded inputs listed in its prompt. It writes its named artifact and a compact verdict object. It must not silently perform another agent's responsibility.

## Default Output Set

- `task_card.json`
- `claim_ledger.json`
- `fact_check_report.md`
- `evidence_registry.json`
- `argument_map.json`
- `logic_report.md`
- `logic_gate.json`
- `structure_plan.md`
- `style_profile.json`
- `style_pass.md`
- `semantic_diff.json`
- `style_gate.json`
- `line_edit.md`
- `risk_report.md`
- `change_log.md`
- `final_draft.md`
- `final_verdict.json`

The local runner may also write diagnostic files such as `logic_report.json`, `agent_verdicts.json`, and `run_summary.md`. The required contract is the default output set above.

## Publication Style

Publication style means technically precise, data-literate, strategically aware, human, calm, and unsentimental prose. It removes inflated claims and empty summary phrases. It keeps judgement clear without pretending certainty where evidence is weak.

Korean publication style favours:

- one main thought per paragraph;
- concrete nouns over vague abstractions;
- restrained confidence;
- clear distinction between claim, evidence, interpretation, and recommendation;
- natural rhythm rather than polished AI uniformity.

English publication style favours:

- British spelling and phrasing;
- direct but non-hyped judgement;
- readable expert prose;
- fewer inflated adjectives;
- explicit uncertainty when evidence is limited.
