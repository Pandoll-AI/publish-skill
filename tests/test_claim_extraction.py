import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from extract_claims import extract_claims  # noqa: E402


def test_extracts_numbers_dates_current_and_high_risk_claims():
    text = "현재 이 투자 전략은 2024년 이후 수익률을 30% 높였다고 알려져 있다. 따라서 모든 투자자는 반드시 도입해야 한다."
    claims = extract_claims(text)["claims"]
    joined_types = {t for c in claims for t in c["claim_type"]}
    assert "number_or_date" in joined_types
    assert "current_state" in joined_types
    assert "high_risk_domain" in joined_types
    assert any(c["needs_verification"] for c in claims)
