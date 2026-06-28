#!/usr/bin/env python3
"""Deterministic scaffold for Publish Skill.

The full skill is intended for agent/LLM execution. This script proves that the
package has a working artifact flow and conservative safety gates without
requiring any network access or third-party packages.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_claims import extract_claims, split_sentences  # noqa: E402

STATUS_ORDER = {"pass": 0, "conditional_pass": 1, "revise_required": 2, "fail": 3}
KOREAN_RE = re.compile(r"[가-힣]")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
ALL_MODES = [
    "audit_only",
    "light_edit",
    "quick_polish",
    "standard_publish",
    "publish_gate",
    "strong_rewrite",
    "publish_ready",
    "high_risk_review",
    "voice_rewrite",
    "explain_for_beginner",
    "fact_check_only",
    "publication_style_only",
    "logic_only",
]
REWRITE_DISABLED_MODES = {"audit_only", "fact_check_only", "logic_only"}
SOFT_GATE_MODES = {"quick_polish", "voice_rewrite", "explain_for_beginner"}
STRICT_GATE_MODES = {"publish_ready", "publish_gate", "high_risk_review"}
STYLE_SPLIT_MODES = {"standard_publish", "strong_rewrite", "publish_ready", "publish_gate", "high_risk_review", "voice_rewrite", "explain_for_beginner"}

AI_PHRASES_KO = [
    "다양한 관점에서 살펴볼 필요가 있다",
    "~하는 데 있어",
]
AI_REPLACEMENTS_KO = {
    "매우 혁신적인 패러다임 전환이라고 할 수 있다": "중요한 변화다",
    "매우 혁신적인 패러다임 전환이라고 할 수 있습니다": "중요한 변화입니다",
    "패러다임 전환이라고 할 수 있다": "큰 변화다",
    "패러다임 전환이라고 할 수 있습니다": "큰 변화입니다",
    "중요한 시사점을 제공한다": "핵심을 짚는다",
    "중요한 시사점을 제공합니다": "핵심을 짚습니다",
    "라고 할 수 있다": "다",
    "라고 할 수 있습니다": "입니다",
    "매우 ": "",
    "이러한 ": "이 ",
    "이를 통해 ": "그 결과 ",
    "데 있어": "때",
}
AI_PHRASES_EN = [
    "it is important to note that",
]
AI_REPLACEMENTS_EN = {
    "for every organization": "for many organisations",
    "for every organisation": "for many organisations",
    "adopting the latest models immediately": "adopting the latest models and where they genuinely fit",
    "in today's fast-paced world, ": "",
    "in today's fast-paced world": "",
    "game-changing paradigm shift": "significant development",
    "game-changing": "significant",
    "revolutionary": "substantial",
    "paradigm shift": "large change",
    "unlock the power of": "use",
}
BRITISH_REPLACEMENTS = {
    "analyze": "analyse",
    "analyzed": "analysed",
    "analyzing": "analysing",
    "optimize": "optimise",
    "optimized": "optimised",
    "organization": "organisation",
    "organizations": "organisations",
    "color": "colour",
    "center": "centre",
    "modeling": "modelling",
    "behavior": "behaviour",
}
STRONG_REPLACEMENTS_KO = {
    "모든 ": "많은 ",
    "항상 ": "대체로 ",
    "절대 ": "쉽게 ",
    "반드시 ": "상황에 따라 ",
    "무조건 ": "대체로 ",
    "최고의 ": "주요한 ",
    "가장 ": "상당히 ",
}
STRONG_REPLACEMENTS_EN = {
    "always": "often",
    "never": "rarely",
    "guarantees": "may support",
    "proves": "suggests",
    "best": "strong",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def detect_language(text: str, explicit: str | None) -> str:
    if explicit and explicit != "auto":
        return explicit
    korean_chars = len(KOREAN_RE.findall(text))
    latin_chars = len(re.findall(r"[A-Za-z]", text))
    if korean_chars and latin_chars and min(korean_chars, latin_chars) / max(korean_chars, latin_chars) > 0.25:
        return "mixed"
    if korean_chars > latin_chars:
        return "ko"
    return "en-GB"


def infer_genre(text: str, purpose: str | None) -> str:
    if purpose:
        p = purpose.lower()
        if "email" in p or "메일" in p:
            return "email"
        if "linkedin" in p:
            return "linkedin_post"
        if "proposal" in p or "제안" in p:
            return "proposal"
        if "blog" in p or "블로그" in p:
            return "blog_article"
        if "report" in p or "보고서" in p:
            return "report"
    if len(text) < 1200:
        return "short_form_prose"
    return "article_or_memo"


def infer_risk_level(claims: Dict[str, Any]) -> str:
    if any(c["risk_level"] == "high" for c in claims.get("claims", [])):
        return "high"
    if any(c["needs_verification"] for c in claims.get("claims", [])):
        return "medium"
    return "low"


def build_task_card(text: str, args: argparse.Namespace, claims: Dict[str, Any]) -> Dict[str, Any]:
    language = detect_language(text, args.language)
    return {
        "created_at": now_iso(),
        "language": language,
        "genre": infer_genre(text, args.purpose),
        "audience": args.audience or "general professional readers",
        "purpose": args.purpose or "prepare the draft for publication",
        "mode": args.mode,
        "mode_policy": describe_mode_policy(args.mode),
        "fact_check_mode": args.fact_check,
        "risk_level": infer_risk_level(claims),
        "style_profile": "publication_style_ko" if language == "ko" else "publication_style_en_gb" if language == "en-GB" else "publication_style_mixed",
        "preserve_intent": True,
        "do_not_change": [],
        "known_limits": [
            "This deterministic script cannot perform live web verification.",
            "No citation is considered verified unless supplied by the user or explicitly checked by an external agent.",
        ],
    }


def describe_mode_policy(mode: str) -> str:
    policies = {
        "quick_polish": "Use light, safety-preserving edits; report non-high-risk gate issues without blocking all rewriting.",
        "standard_publish": "Run the normal publication pipeline with fact, logic, style, risk, and verdict artifacts.",
        "publish_gate": "Require passing logic, style, semantic, source, and evidence gates before final pass.",
        "high_risk_review": "Treat unsupported medical, legal, financial, safety, or public-policy claims as blockers.",
        "voice_rewrite": "Prioritise authorial voice preservation while preventing claim strengthening or source invention.",
        "explain_for_beginner": "Simplify concepts with accurate analogies and explicit limits without adding external sources.",
    }
    return policies.get(mode, "Use the standard configured mode behavior.")


def load_sources(path: Path | None, draft_text: str) -> Dict[str, Any]:
    sources: List[Dict[str, Any]] = []
    if path and path.exists():
        raw = path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                sources.extend(data.get("sources", []))
            elif isinstance(data, list):
                sources.extend(data)
        except json.JSONDecodeError:
            for i, url in enumerate(URL_RE.findall(raw), start=1):
                sources.append({"id": f"S{i:03d}", "title": "User supplied URL", "url": url, "supports": [], "notes": "parsed from text source file"})
    # URLs in draft are references, not proof. We record them but do not treat them as direct support.
    existing_urls = {s.get("url") for s in sources}
    for url in URL_RE.findall(draft_text):
        if url not in existing_urls:
            sources.append({"id": f"DURL{len(sources)+1:03d}", "title": "URL found in draft", "url": url, "supports": [], "notes": "URL present in draft; not automatically verified"})
    return {"sources": sources}


def source_support_lookup(sources: Dict[str, Any]) -> Dict[str, List[str]]:
    lookup: Dict[str, List[str]] = {}
    for source in sources.get("sources", []):
        sid = str(source.get("id", ""))
        for claim_id in source.get("supports", []) or []:
            lookup.setdefault(str(claim_id), []).append(sid)
    return lookup


def fact_check_and_registry(claims: Dict[str, Any], sources: Dict[str, Any], task_card: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    support_lookup = source_support_lookup(sources)
    verified: List[str] = []
    unverified: List[str] = []
    current_needed: List[str] = []
    weaken_or_remove: List[str] = []
    high_risk: List[str] = []
    entries: List[Dict[str, Any]] = []

    for c in claims.get("claims", []):
        cid = c["claim_id"]
        support_ids = support_lookup.get(cid, [])
        if not c["needs_verification"]:
            status = "not_applicable"
            handling = "keep"
            notes = "Opinion, interpretation, or low-risk prose; direct factual verification not required."
        elif support_ids:
            status = "supported"
            handling = "keep"
            notes = "Marked as supported by user-supplied source metadata."
            verified.append(f"- **{cid}**: {c['text']}")
        elif "current_state" in c.get("claim_type", []) and task_card["fact_check_mode"] in {"mixed", "web-required"}:
            status = "needs_current_check"
            handling = "mark_for_review"
            notes = "Current/latest claim needs live verification; no checked source was available to this script."
            current_needed.append(f"- **{cid}**: {c['text']}")
        else:
            status = "unsupported"
            handling = "weaken" if c["strength"] != "high" else "mark_for_review"
            notes = "No supporting source was supplied or verified."
            unverified.append(f"- **{cid}**: {c['text']}")

        if c["risk_level"] == "high":
            high_risk.append(f"- **{cid}** ({status}): {c['text']}")
        if status in {"unsupported", "needs_current_check", "contradicted"} and (c["strength"] == "high" or c["risk_level"] == "high"):
            weaken_or_remove.append(f"- **{cid}**: {c['text']}")

        source_summary = ""
        if support_ids:
            titles = []
            for sid in support_ids:
                match = next((s for s in sources.get("sources", []) if str(s.get("id")) == sid), None)
                titles.append(match.get("title", sid) if match else sid)
            source_summary = "; ".join(titles)

        entries.append({
            "claim_id": cid,
            "support_status": status,
            "evidence_ids": support_ids,
            "source_summary": source_summary,
            "verification_notes": notes,
            "allowed_final_handling": handling,
        })

    report = [
        "# Fact Check Report",
        "",
        "This scaffold does not perform live web verification. It records supplied evidence and marks everything else conservatively.",
        "",
        "## Verified claims",
        "\n".join(verified) if verified else "None verified by supplied source metadata.",
        "",
        "## Unverified claims",
        "\n".join(unverified) if unverified else "No unsupported non-current claims detected.",
        "",
        "## Claims requiring current external verification",
        "\n".join(current_needed) if current_needed else "No current-state claim requiring live verification detected.",
        "",
        "## Claims that should be weakened or removed",
        "\n".join(weaken_or_remove) if weaken_or_remove else "No strong unsupported claim requires immediate removal in this scaffold run.",
        "",
        "## High-risk claims",
        "\n".join(high_risk) if high_risk else "No high-risk claim detected.",
    ]
    return "\n".join(report), {"entries": entries, "sources": sources.get("sources", [])}


def normalise_sentence(s: str) -> str:
    return re.sub(r"\W+", "", s.lower())


def detect_logic_issues(text: str, claims: Dict[str, Any], evidence_registry: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    repairs: List[str] = []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    evidence_by_id = {e["claim_id"]: e for e in evidence_registry.get("entries", [])}

    for c in claims.get("claims", []):
        e = evidence_by_id.get(c["claim_id"], {})
        if c["strength"] == "high" and e.get("support_status") in {"unsupported", "needs_current_check"}:
            issues.append({
                "type": "overclaim",
                "claim_id": c["claim_id"],
                "detail": "Claim strength exceeds available support.",
                "text": c["text"],
            })
            repairs.append(f"Weaken {c['claim_id']} or add evidence before publication.")
        if "causal" in c.get("claim_type", []) and e.get("support_status") != "supported":
            issues.append({
                "type": "causal_leap",
                "claim_id": c["claim_id"],
                "detail": "Causal wording needs direct evidence or softer framing.",
                "text": c["text"],
            })
            repairs.append(f"Frame {c['claim_id']} as association, interpretation, or hypothesis unless evidence is supplied.")

    for idx, p in enumerate(paragraphs, start=1):
        sentence_count = len(split_sentences(p))
        if len(p) > 650 or sentence_count > 6:
            issues.append({"type": "long_paragraph", "paragraph": idx, "detail": "Paragraph may carry too many ideas."})
            repairs.append(f"Split paragraph {idx} and give each paragraph one main idea.")

    seen: Dict[str, str] = {}
    for c in claims.get("claims", []):
        key = normalise_sentence(c["text"])
        if len(key) < 20:
            continue
        if key in seen:
            issues.append({"type": "repetition", "claim_id": c["claim_id"], "detail": f"Repeats {seen[key]}."})
            repairs.append(f"Remove or merge repeated claim {c['claim_id']}.")
        else:
            seen[key] = c["claim_id"]

    first_para = paragraphs[0] if paragraphs else ""
    if first_para and len(first_para) > 120 and not re.search(r"핵심|주장|문제|필요|argument|thesis|point|problem|question", first_para, re.IGNORECASE):
        issues.append({"type": "weak_opening", "detail": "Opening may delay the central point."})
        repairs.append("Move the central claim closer to the opening.")

    last_para = paragraphs[-1] if paragraphs else ""
    if last_para and not re.search(r"결국|핵심|따라서|그래서|마지막|in short|therefore|the point|ultimately|what matters", last_para, re.IGNORECASE):
        issues.append({"type": "weak_ending", "detail": "Ending may not leave a clear final judgement."})
        repairs.append("End with a concise judgement or next action, not a generic summary.")

    thesis = split_sentences(first_para)[0] if first_para and split_sentences(first_para) else "Central thesis not explicit."
    recommended_flow = [
        "Open with the practical question or central judgement.",
        "Separate factual claims from interpretation.",
        "Present the main reasoning in two to four clear moves.",
        "Add caveats where evidence is incomplete.",
        "Close with a specific judgement or action for the reader.",
    ]
    return {"core_thesis": thesis, "issues": issues, "repairs": sorted(set(repairs)), "recommended_flow": recommended_flow}


def conclusion_strength_from_claims(claims: Dict[str, Any]) -> str:
    strengths = [c.get("strength", "medium") for c in claims.get("claims", [])]
    if "high" in strengths:
        return "high"
    if "medium" in strengths:
        return "medium"
    return "low"


def evidence_strength_from_registry(registry: Dict[str, Any]) -> str:
    entries = registry.get("entries", [])
    if not entries:
        return "low"
    supported = sum(1 for e in entries if e.get("support_status") in {"supported", "not_applicable"})
    ratio = supported / max(len(entries), 1)
    if ratio >= 0.85:
        return "high"
    if ratio >= 0.55:
        return "medium"
    return "low"


def build_argument_map(claims: Dict[str, Any], registry: Dict[str, Any], logic: Dict[str, Any]) -> Dict[str, Any]:
    entries_by_id = {e["claim_id"]: e for e in registry.get("entries", [])}
    supporting_claim_ids = [
        c["claim_id"]
        for c in claims.get("claims", [])
        if "opinion" not in c.get("claim_type", []) and len(c.get("text", "")) > 20
    ][:8]
    explicit_premises = [
        c["claim_id"]
        for c in claims.get("claims", [])
        if any(t in c.get("claim_type", []) for t in ["causal", "recommendation", "prediction"])
    ]
    hidden_premises = []
    counterarguments_needed = []
    for c in claims.get("claims", []):
        entry = entries_by_id.get(c["claim_id"], {})
        if c.get("strength") == "high" and entry.get("support_status") in {"unsupported", "needs_current_check"}:
            hidden_premises.append(f"{c['claim_id']}: strong conclusion requires a premise or evidence not present in the draft.")
        if c.get("risk_level") == "high" or c.get("strength") == "high":
            counterarguments_needed.append(c["claim_id"])
    return {
        "central_thesis": logic.get("core_thesis", "Central thesis not explicit."),
        "supporting_claim_ids": supporting_claim_ids,
        "explicit_premises": explicit_premises,
        "hidden_premises": hidden_premises,
        "evidence_strength": evidence_strength_from_registry(registry),
        "conclusion_strength": conclusion_strength_from_claims(claims),
        "counterarguments_needed": sorted(set(counterarguments_needed)),
    }


def build_logic_gate(argument_map: Dict[str, Any], logic: Dict[str, Any], claims: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Any]:
    blockers: List[str] = []
    required_repairs = list(logic.get("repairs", []))
    entries_by_id = {e["claim_id"]: e for e in registry.get("entries", [])}
    for c in claims.get("claims", []):
        entry = entries_by_id.get(c["claim_id"], {})
        if c.get("risk_level") == "high" and entry.get("support_status") != "supported":
            blockers.append(f"{c['claim_id']}: high-risk claim lacks verified support.")
        if c.get("strength") == "high" and entry.get("support_status") in {"unsupported", "needs_current_check"}:
            blockers.append(f"{c['claim_id']}: conclusion strength exceeds available support.")
    if any(i.get("type") == "causal_leap" for i in logic.get("issues", [])):
        required_repairs.append("Repair or soften causal language before publication-style rewriting.")
    if argument_map.get("hidden_premises"):
        required_repairs.append("Make hidden premises explicit or narrow the conclusion.")
    if blockers:
        status = "revise_required"
    elif required_repairs:
        status = "conditional_pass"
    else:
        status = "pass"
    return {
        "status": status,
        "blockers": sorted(set(blockers)),
        "required_repairs": sorted(set(required_repairs)),
        "may_proceed_to_style": status != "revise_required",
        "retry_allowed": status != "pass",
    }


def logic_report_markdown(logic: Dict[str, Any]) -> str:
    issue_lines = [f"- **{i.get('type')}**: {i.get('detail')}" + (f" — {i.get('text')}" if i.get('text') else "") for i in logic.get("issues", [])]
    repair_lines = [f"- {r}" for r in logic.get("repairs", [])]
    flow_lines = [f"{idx}. {step}" for idx, step in enumerate(logic.get("recommended_flow", []), start=1)]
    return "\n".join([
        "# Logic Report",
        "",
        "## Core thesis",
        logic.get("core_thesis", ""),
        "",
        "## Detected logic issues",
        "\n".join(issue_lines) if issue_lines else "No major logic issue detected by the scaffold.",
        "",
        "## Required repairs",
        "\n".join(repair_lines) if repair_lines else "No required repair.",
        "",
        "## Suggested revised argument flow",
        "\n".join(flow_lines),
    ])


def structure_plan_markdown(logic: Dict[str, Any], task_card: Dict[str, Any]) -> str:
    return "\n".join([
        "# Structure Plan",
        "",
        f"Purpose: {task_card['purpose']}",
        f"Audience: {task_card['audience']}",
        "",
        "## Recommended opening",
        "Start with the practical tension or judgement, not a generic introduction.",
        "",
        "## Paragraph sequence",
        "1. State the core claim in plain language.",
        "2. Clarify the evidence or limits of the evidence.",
        "3. Explain the reasoning step by step.",
        "4. Address caveats or counterarguments.",
        "5. End with the action, judgement, or takeaway.",
        "",
        "## What to merge",
        "Merge repeated claims and paragraphs that restate the same point without adding evidence.",
        "",
        "## What to cut",
        "Cut empty setup phrases, unsupported certainty, and decorative adjectives.",
        "",
        "## Where to add caveat or counterpoint",
        "Add caveats near claims marked unsupported or requiring current verification.",
        "",
        "## Recommended ending",
        "Close with a concrete judgement that is no stronger than the evidence allows.",
    ])


def replace_case_insensitive(text: str, old: str, new: str) -> str:
    return re.sub(re.escape(old), new, text, flags=re.IGNORECASE)


def apply_style(text: str, language: str) -> Tuple[str, List[str]]:
    edited = text
    notes: List[str] = []
    if language in {"ko", "mixed"}:
        # Rewrite common empty opener patterns rather than deleting fragments.
        pattern = re.compile(r"본 글은\s*([^\n.。]+?)에 대한 중요한 시사점을 제공한다[.]?")
        if pattern.search(edited):
            edited = pattern.sub(lambda m: f"{m.group(1)}을 다시 볼 필요가 있다.", edited)
            notes.append("Rewrote generic Korean opener: '본 글은 ... 시사점을 제공한다'.")
        pattern_polite = re.compile(r"본 글은\s*([^\n.。]+?)에 대한 중요한 시사점을 제공합니다[.]?")
        if pattern_polite.search(edited):
            edited = pattern_polite.sub(lambda m: f"{m.group(1)}을 다시 볼 필요가 있습니다.", edited)
            notes.append("Rewrote generic Korean polite opener: '본 글은 ... 시사점을 제공합니다'.")
        if "본 글은" in edited:
            edited = edited.replace("본 글은", "이 글은")
            notes.append("Replaced stiff Korean opener: 본 글은 -> 이 글은")
        for old, new in AI_REPLACEMENTS_KO.items():
            if old in edited:
                edited = edited.replace(old, new)
                notes.append(f"Softened/replaced Korean phrase: {old} -> {new}")
        for phrase in AI_PHRASES_KO:
            if phrase in edited:
                edited = edited.replace(phrase, "구체적으로 봐야 한다")
                notes.append(f"Replaced Korean AI-style phrase: {phrase}")
    if language in {"en-GB", "mixed"}:
        for old, new in AI_REPLACEMENTS_EN.items():
            pattern = re.compile(re.escape(old), re.IGNORECASE)
            if pattern.search(edited):
                edited = pattern.sub(new, edited)
                notes.append(f"Replaced English AI/hype phrase: {old} -> {new}")
        # Rewrite self-referential article openers instead of deleting them.
        pattern = re.compile(r"This article explores why ([^.]+)\.", re.IGNORECASE)
        if pattern.search(edited):
            edited = pattern.sub(lambda m: f"The practical question is whether {m.group(1)}.", edited)
            notes.append("Rewrote English self-referential opener: 'This article explores why ...'.")
        low = edited.lower()
        for phrase in AI_PHRASES_EN:
            if phrase in low:
                edited = replace_case_insensitive(edited, phrase, "")
                notes.append(f"Removed English AI phrase: {phrase}")
        # Clean leading punctuation left by removed openers.
        edited = re.sub(r"(^|\n)\s*,\s*", r"\1", edited)
        for old, new in BRITISH_REPLACEMENTS.items():
            # Match whole words only.
            pattern = re.compile(rf"\b{re.escape(old)}\b", re.IGNORECASE)
            if pattern.search(edited):
                edited = pattern.sub(lambda m: new.capitalize() if m.group(0)[0].isupper() else new, edited)
                notes.append(f"Applied British spelling: {old} -> {new}")
    # Remove excessive whitespace created by phrase deletion.
    edited = re.sub(r"[ \t]{2,}", " ", edited)
    edited = re.sub(r"\n{3,}", "\n\n", edited).strip()
    if not notes:
        notes.append("No obvious AI-style cliché or British-spelling issue detected by the scaffold.")
    return edited, notes


def build_style_profile(text: str, language: str) -> Dict[str, Any]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sentences = split_sentences(text)
    avg_sentence_chars = round(sum(len(s) for s in sentences) / max(len(sentences), 1), 1)
    avg_paragraph_chars = round(sum(len(p) for p in paragraphs) / max(len(paragraphs), 1), 1)
    text_l = text.lower()
    preserve_terms = []
    preserve_terms.extend(sorted(set(URL_RE.findall(text))))
    preserve_terms.extend(sorted(set(re.findall(r"\b[A-Z][A-Za-z0-9&.-]{3,}\b", text)))[:12])
    if language in {"ko", "mixed"}:
        preserve_terms.extend(sorted(set(re.findall(r"[가-힣]{2,}(?:\s+[가-힣]{2,}){0,2}", text)))[:12])
    confidence_level = "high" if _text_has_any(text_l, STRONG_REPLACEMENTS_EN.keys()) or any(k in text for k in STRONG_REPLACEMENTS_KO) else "medium"
    abstraction_level = "high" if any(term in text for term in ["시사점", "패러다임", "혁신", "transformative", "paradigm"]) else "medium"
    return {
        "language": language,
        "voice_traits": ["precise", "measured", "authorial", "evidence-aware"],
        "sentence_rhythm": {
            "sentence_count": len(sentences),
            "avg_sentence_chars": avg_sentence_chars,
        },
        "paragraph_rhythm": {
            "paragraph_count": len(paragraphs),
            "avg_paragraph_chars": avg_paragraph_chars,
        },
        "confidence_level": confidence_level,
        "abstraction_level": abstraction_level,
        "preserve_terms": sorted(set(t for t in preserve_terms if len(t.strip()) >= 2))[:20],
    }


def _text_has_any(text_l: str, terms: Iterable[str]) -> bool:
    return any(term.lower() in text_l for term in terms)


def normalised_claim_text(text: str) -> str:
    return re.sub(r"\W+", "", text.lower())


def build_semantic_diff(original: str, final: str, claims: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Any]:
    final_claims = extract_claims(final)
    original_claim_keys = {normalised_claim_text(c["text"]) for c in claims.get("claims", [])}
    original_urls = set(URL_RE.findall(original))
    final_urls = set(URL_RE.findall(final))
    added_sources = sorted(final_urls - original_urls)
    added_claims = []
    strengthened_claims = []
    removed_key_points = []
    final_text_norm = normalised_claim_text(final)
    for c in final_claims.get("claims", []):
        key = normalised_claim_text(c["text"])
        if key not in original_claim_keys and c.get("needs_verification") and c.get("strength") == "high":
            added_claims.append(c["text"])
    for c in claims.get("claims", []):
        if c.get("strength") == "low":
            continue
        claim_key = normalised_claim_text(c["text"])
        if len(claim_key) > 30 and claim_key not in final_text_norm:
            # This is a conservative signal, not automatic drift: safety rewrites may change wording.
            if c.get("risk_level") == "high" or c.get("strength") == "high":
                removed_key_points.append(c["claim_id"])
    unsupported_ids = {
        e["claim_id"]
        for e in registry.get("entries", [])
        if e.get("support_status") in {"unsupported", "needs_current_check"}
    }
    for c in final_claims.get("claims", []):
        if c.get("strength") == "high" and c.get("needs_verification"):
            if not any(c["text"] in old.get("text", "") for old in claims.get("claims", [])):
                strengthened_claims.append(c["text"])
    semantic_drift = bool(added_claims or strengthened_claims)
    return {
        "semantic_drift": semantic_drift,
        "added_claims": added_claims,
        "strengthened_claims": strengthened_claims,
        "removed_key_points": removed_key_points,
        "meaning_preserved": not semantic_drift,
        "source_added": bool(added_sources),
        "added_sources": added_sources,
        "unsupported_claim_ids_checked": sorted(unsupported_ids),
    }


def build_style_gate(style_notes: List[str], semantic_diff: Dict[str, Any], logic_gate: Dict[str, Any], final_text: str, language: str) -> Dict[str, Any]:
    remaining_issues: List[str] = []
    if logic_gate.get("status") == "revise_required":
        remaining_issues.append("Logic gate has blockers; publication-style polish is not allowed yet.")
    if semantic_diff.get("semantic_drift"):
        remaining_issues.append("Semantic drift detected in style candidate.")
    if semantic_diff.get("source_added"):
        remaining_issues.append("External source or URL was added during rewriting.")
    if language in {"ko", "mixed"} and any(phrase in final_text for phrase in AI_REPLACEMENTS_KO):
        remaining_issues.append("Korean AI-style phrase remains.")
    if language in {"en-GB", "mixed"} and any(phrase.lower() in final_text.lower() for phrase in AI_REPLACEMENTS_EN):
        remaining_issues.append("English AI/hype phrase remains.")
    if semantic_diff.get("semantic_drift") or semantic_diff.get("source_added") or logic_gate.get("status") == "revise_required":
        status = "revise_required"
    elif remaining_issues:
        status = "conditional_pass"
    else:
        status = "pass"
    style_score = max(0.0, 0.9 - 0.12 * len(remaining_issues))
    readability_score = 0.86 if style_notes else 0.78
    return {
        "status": status,
        "style_score": round(style_score, 2),
        "readability_score": round(readability_score, 2),
        "semantic_drift": bool(semantic_diff.get("semantic_drift")),
        "source_added": bool(semantic_diff.get("source_added")),
        "remaining_issues": remaining_issues,
        "retry_allowed": status != "pass",
    }


def has_high_risk_logic_blocker(logic_gate: Dict[str, Any]) -> bool:
    return any("high-risk" in str(blocker).lower() for blocker in logic_gate.get("blockers", []))


def may_rewrite_with_logic_gate(mode: str, logic_gate: Dict[str, Any]) -> bool:
    if logic_gate.get("status") != "revise_required":
        return True
    return mode in SOFT_GATE_MODES and not has_high_risk_logic_blocker(logic_gate)


def weaken_text(text: str, language: str) -> Tuple[str, List[str]]:
    edited = text
    notes: List[str] = []
    if language in {"ko", "mixed"}:
        for old, new in STRONG_REPLACEMENTS_KO.items():
            if old in edited:
                edited = edited.replace(old, new)
                notes.append(f"Weakened unsupported certainty: {old.strip()} -> {new.strip()}")
    if language in {"en-GB", "mixed"}:
        phrase_patterns = [
            (r"\bwill\s+(?:optimize|optimise)\s+all\s+knowledge\s+work\b", "may improve some knowledge-work processes"),
            (r"\ball\s+knowledge\s+work\b", "many knowledge-work processes"),
            (r"\bmake\s+traditional\s+software\s+teams\s+obsolete\b", "change how software teams work"),
            (r"\bmust\s+adopt\b", "should consider adopting"),
            (r"\bmust\s+move\b", "should consider moving"),
        ]
        for pattern_text, replacement in phrase_patterns:
            pattern = re.compile(pattern_text, re.IGNORECASE)
            if pattern.search(edited):
                edited = pattern.sub(replacement, edited)
                notes.append(f"Weakened unsupported English phrase: {pattern_text} -> {replacement}")
        for old, new in STRONG_REPLACEMENTS_EN.items():
            pattern = re.compile(rf"\b{re.escape(old)}\b", re.IGNORECASE)
            if pattern.search(edited):
                edited = pattern.sub(lambda m: new.capitalize() if m.group(0)[0].isupper() else new, edited)
                notes.append(f"Weakened unsupported certainty: {old} -> {new}")
    return edited, notes


def apply_fact_safety_to_draft(text: str, claims: Dict[str, Any], registry: Dict[str, Any], language: str) -> Tuple[str, List[str]]:
    edited = text
    notes: List[str] = []
    by_id = {e["claim_id"]: e for e in registry.get("entries", [])}
    for c in claims.get("claims", []):
        entry = by_id.get(c["claim_id"], {})
        status = entry.get("support_status")
        if status in {"unsupported", "needs_current_check"} and c["strength"] == "high":
            weakened, wnotes = weaken_text(c["text"], language)
            if weakened != c["text"] and c["text"] in edited:
                edited = edited.replace(c["text"], weakened)
                notes.append(f"{c['claim_id']}: weakened unsupported strong claim.")
                notes.extend(wnotes)
            elif c["text"] in edited:
                marker = " [검증 필요]" if language in {"ko", "mixed"} else " [verification needed]"
                edited = edited.replace(c["text"], c["text"] + marker)
                notes.append(f"{c['claim_id']}: marked unsupported strong claim for verification.")
        elif status == "needs_current_check" and c["text"] in edited:
            marker = " [최신 확인 필요]" if language in {"ko", "mixed"} else " [current verification needed]"
            if marker not in edited:
                edited = edited.replace(c["text"], c["text"] + marker)
                notes.append(f"{c['claim_id']}: marked current-state claim for verification.")
    if not notes:
        notes.append("No strong unsupported claim was modified by the scaffold.")
    return edited, notes


def line_edit_text(text: str, language: str, mode: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    edited_paragraphs: List[str] = []
    for p in paragraphs:
        p2 = p
        # Simple trimming of repeated spaces and repeated punctuation.
        p2 = re.sub(r"\s+", " ", p2).strip()
        p2 = re.sub(r"([.!?。！？]){2,}", r"\1", p2)
        if language in {"ko", "mixed"} and len(p2) > 580 and mode in STYLE_SPLIT_MODES:
            sentences = split_sentences(p2)
            if len(sentences) > 2:
                midpoint = len(sentences) // 2
                edited_paragraphs.append(" ".join(sentences[:midpoint]).strip())
                edited_paragraphs.append(" ".join(sentences[midpoint:]).strip())
                notes.append("Split a long Korean paragraph to improve reading rhythm.")
                continue
        if language in {"en-GB", "mixed"} and len(p2.split()) > 130 and mode in STYLE_SPLIT_MODES:
            sentences = split_sentences(p2)
            if len(sentences) > 2:
                midpoint = len(sentences) // 2
                edited_paragraphs.append(" ".join(sentences[:midpoint]).strip())
                edited_paragraphs.append(" ".join(sentences[midpoint:]).strip())
                notes.append("Split a long English paragraph to improve reading rhythm.")
                continue
        edited_paragraphs.append(p2)
    if not notes:
        notes.append("Line edit preserved paragraph structure; only whitespace and punctuation were normalised.")
    return "\n\n".join(edited_paragraphs), notes


def make_style_pass(notes: List[str], safety_notes: List[str], style_gate: Dict[str, Any] | None = None) -> str:
    gate_lines = []
    if style_gate:
        gate_lines = [
            "",
            "## Style gate",
            f"- Status: `{style_gate.get('status')}`",
            f"- Semantic drift: `{style_gate.get('semantic_drift')}`",
            *[f"- Remaining issue: {issue}" for issue in style_gate.get("remaining_issues", [])],
        ]
    return "\n".join([
        "# Publication Style Pass",
        "",
        "## Style changes applied",
        *[f"- {n}" for n in notes],
        "",
        "## Factual safety constraints respected",
        *[f"- {n}" for n in safety_notes],
        "",
        "## Voice preservation note",
        "The edit is conservative: it removes cliché and unsupported certainty without replacing the author's central judgement.",
        *gate_lines,
    ])


def make_line_edit_report(final_candidate: str, notes: List[str]) -> str:
    return "\n".join([
        "# Line Edit",
        "",
        "## Edited final candidate",
        final_candidate,
        "",
        "## Line-edit notes",
        *[f"- {n}" for n in notes],
    ])


def risk_bias_report(claims: Dict[str, Any], registry: Dict[str, Any], draft: str) -> Tuple[str, List[str], List[str]]:
    flags: List[str] = []
    mitigations: List[str] = []
    by_id = {e["claim_id"]: e for e in registry.get("entries", [])}
    hype_terms = ["game-changing", "revolutionary", "패러다임", "혁신적인", "최고", "best", "only"]
    if any(t.lower() in draft.lower() for t in hype_terms):
        flags.append("Technology or rhetorical hype may still be present.")
        mitigations.append("Replace hype with concrete evidence-aware language.")
    vendor_terms = ["OpenAI", "Google", "Microsoft", "Anthropic", "Apple", "Samsung", "Meta", "Amazon"]
    if sum(1 for t in vendor_terms if t.lower() in draft.lower()) >= 2:
        flags.append("Multiple vendor names appear; check for company-centred framing.")
        mitigations.append("Compare capabilities or evidence rather than brand reputation.")
    for c in claims.get("claims", []):
        e = by_id.get(c["claim_id"], {})
        if c["risk_level"] == "high" and e.get("support_status") != "supported":
            flags.append(f"High-risk claim {c['claim_id']} is not supported by supplied evidence.")
            mitigations.append(f"Add reliable evidence, weaken, or remove {c['claim_id']}.")
        if c["strength"] == "high" and e.get("support_status") in {"unsupported", "needs_current_check"}:
            flags.append(f"Unsupported certainty remains around {c['claim_id']}.")
            mitigations.append(f"Ensure {c['claim_id']} is softened or visibly marked.")
    residual = flags if flags else ["No major risk or bias flag detected by the scaffold."]
    report = "\n".join([
        "# Risk & Bias Report",
        "",
        "## Risk flags",
        "\n".join(f"- {f}" for f in flags) if flags else "No major risk flag detected.",
        "",
        "## Required mitigations",
        "\n".join(f"- {m}" for m in sorted(set(mitigations))) if mitigations else "No mitigation required by this scaffold.",
        "",
        "## Residual risk",
        "\n".join(f"- {r}" for r in residual),
    ])
    return report, flags, sorted(set(mitigations))


def make_change_log(original: str, final: str, safety_notes: List[str], style_notes: List[str], line_notes: List[str], logic: Dict[str, Any], logic_gate: Dict[str, Any], style_gate: Dict[str, Any]) -> str:
    changed = original.strip() != final.strip()
    major = ["Draft was processed through claim, evidence, logic, style, line-edit, and risk gates."]
    if changed:
        major.append("Final draft differs from the original draft.")
    else:
        major.append("No material rewrite was made by the deterministic scaffold.")
    return "\n".join([
        "# Change Log",
        "",
        "## Major changes",
        *[f"- {m}" for m in major],
        "",
        "## Factual safety changes",
        *[f"- {n}" for n in safety_notes],
        "",
        "## Logic/structure changes",
        *([f"- {r}" for r in logic.get("repairs", [])] or ["- No required logic repair detected by the scaffold."]),
        "",
        "## Gate outcomes",
        f"- Logic gate: `{logic_gate.get('status')}`",
        f"- Style gate: `{style_gate.get('status')}`",
        f"- Semantic drift: `{style_gate.get('semantic_drift')}`",
        "",
        "## Style changes",
        *[f"- {n}" for n in style_notes],
        "",
        "## Line-edit changes",
        *[f"- {n}" for n in line_notes],
        "",
        "## Preserved authorial choices",
        "- The central claim and key terms of the original draft were preserved unless marked for evidence review.",
    ])


def compute_final_verdict(claims: Dict[str, Any], registry: Dict[str, Any], logic: Dict[str, Any], risk_flags: List[str], mode: str, logic_gate: Dict[str, Any], style_gate: Dict[str, Any], semantic_diff: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    warnings: List[str] = []
    entries_by_id = {e["claim_id"]: e for e in registry.get("entries", [])}
    unsupported_count = 0
    current_needed = 0
    high_risk_unsup = 0
    for c in claims.get("claims", []):
        e = entries_by_id.get(c["claim_id"], {})
        status = e.get("support_status")
        if status == "unsupported":
            unsupported_count += 1
            if c["risk_level"] == "high":
                high_risk_unsup += 1
                blocking.append(f"High-risk claim {c['claim_id']} lacks supporting evidence.")
            elif c["strength"] == "high":
                warnings.append(f"Strong claim {c['claim_id']} lacks supporting evidence.")
        elif status == "needs_current_check":
            current_needed += 1
            warnings.append(f"Current-state claim {c['claim_id']} needs live verification.")

    severe_logic = [i for i in logic.get("issues", []) if i.get("type") in {"overclaim", "causal_leap"}]
    if logic_gate.get("status") == "revise_required":
        if mode in SOFT_GATE_MODES and not has_high_risk_logic_blocker(logic_gate):
            status = "conditional_pass"
            warnings.extend(logic_gate.get("blockers", []) or ["Logic gate did not pass; rewrite was limited by soft mode."])
        else:
            status = "revise_required"
            blocking.extend(logic_gate.get("blockers", []) or ["Logic gate did not pass."])
    elif style_gate.get("status") == "revise_required":
        status = "revise_required"
        blocking.extend(style_gate.get("remaining_issues", []) or ["Style gate did not pass."])
    elif semantic_diff.get("semantic_drift"):
        status = "revise_required"
        blocking.append("Semantic drift detected in publication-style pass.")
    elif semantic_diff.get("source_added"):
        status = "revise_required"
        blocking.append("External source or URL was added without an explicit checked-source workflow.")
    elif high_risk_unsup:
        status = "revise_required"
    elif mode in STRICT_GATE_MODES and (unsupported_count or current_needed):
        status = "revise_required"
        blocking.append(f"{mode} mode does not allow unresolved verification gaps.")
    elif risk_flags and any("High-risk" in f or "Unsupported certainty" in f for f in risk_flags):
        status = "revise_required"
    elif unsupported_count or current_needed or severe_logic or logic_gate.get("status") != "pass" or style_gate.get("status") != "pass":
        status = "conditional_pass"
    else:
        status = "pass"

    factuality = max(0.0, 1.0 - (unsupported_count * 0.08) - (current_needed * 0.06) - (high_risk_unsup * 0.25))
    logic_score = max(0.0, 1.0 - min(len(logic.get("issues", [])), 6) * 0.08)
    risk_score = 0.55 if high_risk_unsup else max(0.6, 1.0 - len(risk_flags) * 0.08)
    scores = {
        "factuality": round(factuality, 2),
        "logic": round(logic_score, 2),
        "style": style_gate.get("style_score", 0.0),
        "readability": style_gate.get("readability_score", 0.0),
        "traceability": 0.95,
        "risk": round(risk_score, 2),
    }
    if status == "pass":
        next_action = "Ready for use in the requested context."
    elif status == "conditional_pass":
        next_action = "Review residual warnings, especially unsupported or current-state claims, before public release."
    elif status == "revise_required":
        next_action = "Resolve blocking evidence or logic issues, then rerun the publication pipeline."
    else:
        next_action = "Do not publish until major factual or safety defects are corrected."
    return {
        "status": status,
        "scores": scores,
        "blocking_issues": sorted(set(blocking)),
        "residual_warnings": sorted(set(warnings + risk_flags)),
        "recommended_next_action": next_action,
        "release_note": "Verdict produced by Publish Skill deterministic scaffold. Full LLM execution should apply the same gates with deeper judgement.",
    }


def agent_verdict(agent: str, status: str, confidence: float, blocking: List[str] | None, next_agent: str | None) -> Dict[str, Any]:
    return {
        "agent": agent,
        "status": status,
        "confidence": confidence,
        "blocking_issues": blocking or [],
        "next_agent": next_agent,
    }


def run_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    draft_path: Path = args.draft
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    original = draft_path.read_text(encoding="utf-8")

    agent_verdicts: List[Dict[str, Any]] = []

    # 01 Intake depends on preliminary claims to assess risk, but writes a bounded task card.
    claims = extract_claims(original)
    task_card = build_task_card(original, args, claims)
    write_json(output_dir / "task_card.json", task_card)
    agent_verdicts.append(agent_verdict("01_intake_agent", "pass", 0.9, [], "02_claim_miner_agent"))

    # 02 Claim miner.
    write_json(output_dir / "claim_ledger.json", claims)
    claim_status = "pass" if claims.get("claims") else "conditional_pass"
    agent_verdicts.append(agent_verdict("02_claim_miner_agent", claim_status, 0.72, [] if claims.get("claims") else ["No claims extracted; draft may be too short or non-prose."], "03_fact_check_agent"))

    # 03/04 Fact check and evidence registry.
    sources = load_sources(args.sources, original)
    fact_report, registry = fact_check_and_registry(claims, sources, task_card)
    write_text(output_dir / "fact_check_report.md", fact_report)
    write_json(output_dir / "evidence_registry.json", registry)
    unresolved = [e for e in registry.get("entries", []) if e["support_status"] in {"unsupported", "needs_current_check"}]
    fact_status = "conditional_pass" if unresolved else "pass"
    if any(c["risk_level"] == "high" and registry["entries"][i]["support_status"] != "supported" for i, c in enumerate(claims.get("claims", []))):
        fact_status = "revise_required"
    agent_verdicts.append(agent_verdict("03_fact_check_agent", fact_status, 0.68, ["Unresolved verification gaps exist."] if unresolved else [], "04_evidence_registry_agent"))
    agent_verdicts.append(agent_verdict("04_evidence_registry_agent", "pass", 0.88, [], "05_logic_agent"))

    # 05 Logic and 06 Structure.
    logic = detect_logic_issues(original, claims, registry)
    argument_map = build_argument_map(claims, registry, logic)
    logic_gate = build_logic_gate(argument_map, logic, claims, registry)
    write_json(output_dir / "argument_map.json", argument_map)
    write_json(output_dir / "logic_gate.json", logic_gate)
    write_json(output_dir / "logic_report.json", logic)
    write_text(output_dir / "logic_report.md", logic_report_markdown(logic))
    logic_status = logic_gate["status"]
    agent_verdicts.append(agent_verdict("05_logic_agent", logic_status, 0.76, [], "06_structure_agent"))
    write_text(output_dir / "structure_plan.md", structure_plan_markdown(logic, task_card))
    agent_verdicts.append(agent_verdict("06_structure_agent", "pass", 0.78, [], "07_publication_style_agent"))

    # Apply safety then style then line edit unless audit/fact-only/logic-only mode disables rewrite.
    working = original
    safety_notes: List[str] = []
    style_notes: List[str] = []
    line_notes: List[str] = []
    if not may_rewrite_with_logic_gate(args.mode, logic_gate):
        safety_notes = ["Rewrite restricted because the logic gate has blocking issues."]
        style_notes = ["Publication-style rewrite skipped until logic blockers are repaired."]
        line_notes = ["Line edit restricted because the logic gate did not pass."]
    elif args.mode not in REWRITE_DISABLED_MODES:
        working, safety_notes = apply_fact_safety_to_draft(working, claims, registry, task_card["language"])
        working, style_notes = apply_style(working, task_card["language"])
        working, line_notes = line_edit_text(working, task_card["language"], args.mode)
    else:
        safety_notes = ["Rewrite disabled by mode; factual issues are reported but not edited in the draft."]
        style_notes = ["Style pass disabled by mode."]
        line_notes = ["Line edit disabled by mode."]

    style_profile = build_style_profile(original, task_card["language"])
    semantic_diff = build_semantic_diff(original, working, claims, registry)
    style_gate = build_style_gate(style_notes, semantic_diff, logic_gate, working, task_card["language"])
    write_json(output_dir / "style_profile.json", style_profile)
    write_json(output_dir / "semantic_diff.json", semantic_diff)
    write_json(output_dir / "style_gate.json", style_gate)
    write_text(output_dir / "style_pass.md", make_style_pass(style_notes, safety_notes, style_gate))
    agent_verdicts.append(agent_verdict("07_publication_style_agent", style_gate["status"], 0.74, style_gate.get("remaining_issues", []), "08_line_editor_agent"))
    write_text(output_dir / "line_edit.md", make_line_edit_report(working, line_notes))
    agent_verdicts.append(agent_verdict("08_line_editor_agent", "pass", 0.76, [], "09_risk_bias_agent"))

    risk_report, risk_flags, mitigations = risk_bias_report(claims, registry, working)
    write_text(output_dir / "risk_report.md", risk_report)
    risk_status = "revise_required" if any("High-risk" in f or "Unsupported certainty" in f for f in risk_flags) else "pass"
    agent_verdicts.append(agent_verdict("09_risk_bias_agent", risk_status, 0.75, mitigations if risk_status == "revise_required" else [], "10_diff_rationale_agent"))

    change_log = make_change_log(original, working, safety_notes, style_notes, line_notes, logic, logic_gate, style_gate)
    write_text(output_dir / "change_log.md", change_log)
    agent_verdicts.append(agent_verdict("10_diff_rationale_agent", "pass", 0.84, [], "11_final_architect_agent"))

    final_verdict = compute_final_verdict(claims, registry, logic, risk_flags, args.mode, logic_gate, style_gate, semantic_diff)
    write_json(output_dir / "final_verdict.json", final_verdict)
    agent_verdicts.append(agent_verdict("11_final_architect_agent", final_verdict["status"], 0.82, final_verdict["blocking_issues"], None))

    final_note = ""
    if final_verdict["status"] != "pass":
        if task_card["language"] in {"ko", "mixed"}:
            final_note = "> 편집자 주: 아래 원고에는 검증이 필요한 주장이 남아 있습니다. 공개 전 `fact_check_report.md`와 `final_verdict.json`을 확인하세요.\n\n"
        else:
            final_note = "> Editor's note: this draft still contains claims requiring verification. Review `fact_check_report.md` and `final_verdict.json` before publication.\n\n"
    write_text(output_dir / "final_draft.md", final_note + working)
    write_json(output_dir / "agent_verdicts.json", {"verdicts": agent_verdicts})
    write_text(output_dir / "run_summary.md", "\n".join([
        "# Publish Skill Run Summary",
        "",
        f"Draft: `{draft_path}`",
        f"Mode: `{args.mode}`",
        f"Language: `{task_card['language']}`",
        f"Final status: `{final_verdict['status']}`",
        "",
        "Artifacts written:",
        "- task_card.json",
        "- claim_ledger.json",
        "- fact_check_report.md",
        "- evidence_registry.json",
        "- argument_map.json",
        "- logic_gate.json",
        "- logic_report.md/json",
        "- structure_plan.md",
        "- style_profile.json",
        "- style_pass.md",
        "- semantic_diff.json",
        "- style_gate.json",
        "- line_edit.md",
        "- risk_report.md",
        "- change_log.md",
        "- final_draft.md",
        "- final_verdict.json",
    ]))
    return {
        "ok": final_verdict["status"] in {"pass", "conditional_pass", "revise_required"},
        "output_dir": str(output_dir),
        "status": final_verdict["status"],
        "claims": len(claims.get("claims", [])),
        "unresolved_claims": len(unresolved),
        "artifacts": sorted(p.name for p in output_dir.iterdir() if p.is_file()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Publish Skill artifact pipeline on a draft.")
    parser.add_argument("--draft", type=Path, required=True, help="Path to the draft markdown/text file.")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for artifacts.")
    parser.add_argument("--language", default="auto", choices=["auto", "ko", "en-GB", "mixed"], help="Draft language. Default: auto.")
    parser.add_argument("--purpose", default=None, help="Purpose/genre, e.g. blog article, proposal, memo.")
    parser.add_argument("--audience", default=None, help="Target audience.")
    parser.add_argument("--mode", default="standard_publish", choices=ALL_MODES, help="Publication mode.")
    parser.add_argument("--fact-check", default="mixed", choices=["no-web", "web-required", "user-sources-only", "mixed"], help="Fact-check policy.")
    parser.add_argument("--sources", type=Path, default=None, help="Optional JSON source metadata. Sources can include `supports`: [claim_id].")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.draft.exists():
        print(json.dumps({"ok": False, "error": f"Draft not found: {args.draft}"}, ensure_ascii=False), file=sys.stderr)
        return 2
    summary = run_pipeline(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
