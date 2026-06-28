#!/usr/bin/env python3
"""Heuristic claim extraction for Publish Skill.

This module is intentionally conservative. It does not verify claims and it does
not create evidence. Its job is to identify statements that should be reviewed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Iterable, List, Dict, Any

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？다요죠임함됨음])\s+|\n+")
NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:%|percent|per cent|년|월|일|명|개|배|x|times|million|billion|조|억|만)?\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b|\b\d{4}년\b")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
CAP_ENTITY_RE = re.compile(r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,4}\b")

CURRENT_TERMS = {
    "current", "currently", "now", "today", "recent", "recently", "latest", "newest", "as of",
    "현재", "최근", "요즘", "지금", "최신", "오늘", "현시점", "가장 많이", "가장 큰",
}
CAUSAL_TERMS = {
    "because", "therefore", "due to", "causes", "caused", "leads to", "resulting in", "as a result",
    "때문", "따라서", "이로 인해", "결과적으로", "초래", "야기", "덕분", "로 인해",
}
HIGH_RISK_TERMS = {
    "diagnosis", "treatment", "clinical", "patient", "mortality", "drug", "dose", "surgery",
    "legal", "law", "compliance", "regulation", "liability", "rights",
    "investment", "stock", "return", "portfolio", "profit", "loss", "financial", "tax",
    "진단", "치료", "환자", "사망", "약물", "수술", "임상", "의학", "의료",
    "법", "규제", "준법", "법적 책임", "권리", "소송",
    "투자", "주식", "수익", "손실", "포트폴리오", "금융", "세금",
}
STRONG_TERMS = {
    "always", "never", "all", "none", "must", "proves", "guarantees", "best", "most", "only",
    "항상", "절대", "모든", "반드시", "증명", "보장", "최고", "가장", "유일", "무조건",
}
WEAKENING_TERMS = {
    "may", "might", "could", "likely", "plausible", "suggests", "appears", "in some cases",
    "가능", "수 있다", "보인다", "일부", "추정", "시사", "듯하다", "것 같다",
}
OPINION_TERMS = {
    "i think", "i believe", "in my view", "my view", "i argue", "i prefer",
    "내 생각", "나는", "제가 보기", "개인적으로", "라고 본다", "라고 생각",
}
PREDICTION_TERMS = {
    "will", "future", "next", "by 20", "forecast", "expect", "예상", "전망", "앞으로", "향후", "될 것이다", "가능성이 크다",
}
RECOMMENDATION_TERMS = {
    "should", "need to", "must", "recommend", "권고", "해야", "필요", "추천", "바람직",
}

@dataclass
class Claim:
    claim_id: str
    text: str
    claim_type: List[str]
    risk_level: str
    strength: str
    needs_verification: bool
    reason: str
    location_hint: str


def _contains_any(text_l: str, terms: Iterable[str]) -> bool:
    return any(term in text_l for term in terms)


def split_sentences(text: str) -> List[str]:
    """Split prose into sentence-like units without requiring NLP packages."""
    raw = [s.strip(" \t\r\n-•") for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]
    # Merge very short fragments with the previous sentence to avoid noisy bullets.
    merged: List[str] = []
    for s in raw:
        if merged and len(s) < 18 and not re.search(r"[.!?。！？]$", merged[-1]):
            merged[-1] = f"{merged[-1]} {s}".strip()
        else:
            merged.append(s)
    return merged


def classify_sentence(sentence: str) -> Dict[str, Any]:
    text_l = sentence.lower()
    claim_types: List[str] = []
    reasons: List[str] = []

    if URL_RE.search(sentence):
        claim_types.append("source_reference")
        reasons.append("contains URL-like reference")
    if NUMBER_RE.search(sentence) or YEAR_RE.search(sentence):
        claim_types.append("number_or_date")
        reasons.append("contains number, percentage, date, or year")
    if _contains_any(text_l, CURRENT_TERMS):
        claim_types.append("current_state")
        reasons.append("contains current/latest/recent wording")
    if _contains_any(text_l, CAUSAL_TERMS):
        claim_types.append("causal")
        reasons.append("contains causal language")
    if _contains_any(text_l, HIGH_RISK_TERMS):
        claim_types.append("high_risk_domain")
        reasons.append("touches a high-risk domain")
    if _contains_any(text_l, PREDICTION_TERMS):
        claim_types.append("prediction")
        reasons.append("contains predictive wording")
    if _contains_any(text_l, RECOMMENDATION_TERMS):
        claim_types.append("recommendation")
        reasons.append("contains recommendation or obligation wording")
    if _contains_any(text_l, OPINION_TERMS):
        claim_types.append("opinion")
        reasons.append("contains explicit author viewpoint")
    if CAP_ENTITY_RE.search(sentence) and not sentence.isupper():
        # Avoid treating first-word capitalisation alone as a named entity by checking for substantial tokens.
        entities = [m.group(0) for m in CAP_ENTITY_RE.finditer(sentence)]
        if any(len(e) > 3 for e in entities):
            claim_types.append("named_entity")
            reasons.append("contains named entity-like wording")

    if not claim_types and len(sentence) > 25:
        # Long declarative sentences often carry an interpretive claim.
        claim_types.append("interpretation")
        reasons.append("substantial interpretive or explanatory statement")

    if _contains_any(text_l, HIGH_RISK_TERMS):
        risk = "high"
    elif any(t in claim_types for t in ["number_or_date", "current_state", "causal", "named_entity", "prediction", "recommendation"]):
        risk = "medium"
    else:
        risk = "low"

    if _contains_any(text_l, STRONG_TERMS):
        strength = "high"
    elif _contains_any(text_l, WEAKENING_TERMS) or "opinion" in claim_types:
        strength = "low"
    else:
        strength = "medium"

    needs_verification = any(t in claim_types for t in [
        "number_or_date", "current_state", "causal", "named_entity", "high_risk_domain"
    ]) and "opinion" not in claim_types

    return {
        "claim_type": sorted(set(claim_types)),
        "risk_level": risk,
        "strength": strength,
        "needs_verification": needs_verification,
        "reason": "; ".join(reasons) if reasons else "not a check-worthy claim",
    }


def extract_claims(text: str) -> Dict[str, List[Dict[str, Any]]]:
    sentences = split_sentences(text)
    claims: List[Claim] = []
    for idx, sentence in enumerate(sentences, start=1):
        info = classify_sentence(sentence)
        # Ignore tiny fragments and headings unless they contain hard facts.
        if len(sentence) < 12 and not info["needs_verification"]:
            continue
        claim = Claim(
            claim_id=f"C{len(claims)+1:03d}",
            text=sentence,
            claim_type=info["claim_type"],
            risk_level=info["risk_level"],
            strength=info["strength"],
            needs_verification=info["needs_verification"],
            reason=info["reason"],
            location_hint=f"sentence_{idx}",
        )
        claims.append(claim)
    return {"claims": [asdict(c) for c in claims]}


if __name__ == "__main__":
    import argparse, json, pathlib
    parser = argparse.ArgumentParser(description="Extract check-worthy claims from a draft.")
    parser.add_argument("draft", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    data = extract_claims(args.draft.read_text(encoding="utf-8"))
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
