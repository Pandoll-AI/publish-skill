<h1 align="center">Publish Skill</h1>

<p align="center">
  <a href="README.en.md"><img alt="Read in English" src="https://img.shields.io/badge/Read%20in-English-111827?style=for-the-badge"></a>
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

<p align="center"><strong>Publish Skill은 초안을 바로 예쁘게 고치는 도구가 아닙니다.</strong></p>

<p align="center">먼저 주장을 분리하고, 근거 빈칸과 논리 위험을 표시한 뒤, 안전한 범위에서만 문장을 다듬는 출판 전 워크플로 스캐폴드입니다.</p>

<p align="center"><strong>현재 성숙도: v0.3.0 scaffold.</strong> 로컬 러너는 실시간 웹 검증이나 깊은 의미 판정을 수행하지 않습니다.</p>

## 왜 필요한가

대부분의 글쓰기 도구는 문장을 너무 빨리 다듬습니다. 그 결과 논리 비약, 과장, 출처 없는 수치, AI식 상투구가 더 매끈한 문장 안에 숨어버립니다.

Publish Skill은 반대로 움직입니다.

```text
주장 추출 -> 근거 빈칸 표시 -> 논리 게이트 -> 문체 패스 -> 표면 claim diff -> 최종 판정
```

그래서 보고서, 칼럼, 제안서, 연설문, 블로그 글, LinkedIn 글처럼 “좋아 보이는 문장”보다 “검증할 지점이 드러난 글”이 중요한 작업에 맞습니다.

## 핵심 기능

- 사실, 해석, 의견, 전망, 추천을 휴리스틱하게 분리합니다.
- unsupported claim, current-state claim, high-risk claim을 보수적으로 표시합니다.
- overclaim, causal leap, unsupported certainty, 약한 도입부와 결론을 1차 필터로 잡습니다.
- 논리 게이트가 막히면 강한 문체 polish를 제한합니다.
- 글쓴이의 관점과 목소리를 보존하면서 AI스러운 리듬을 줄입니다.
- `claim_ledger`, `evidence_registry`, `logic_gate`, `style_gate`, `final_verdict`를 포함한 검토 산출물을 남깁니다.
- 사용자가 요청하거나 제공하지 않은 출처, 링크, 논문명, 통계, 기관명을 만들지 않습니다.

## 하지 않는 일

- 로컬 러너는 실시간 웹 검색을 하지 않습니다.
- Codex agent 실행에서는 사용자가 요청하고 도구가 가능할 때 외부 검증을 별도 단계로 수행할 수 있습니다.
- URL이 원고에 있다는 이유만으로 검증된 출처로 보지 않습니다.
- supplied source metadata의 `supports`는 기록용 신호이며, 본문과 claim의 직접 지지를 자동 판정하지 않습니다.
- `semantic_diff.json`은 표면 claim 비교입니다. NLI나 entailment judge가 아닙니다.
- `final_verdict.json`의 `heuristic_scores`는 보정된 품질 점수가 아니라 규칙 기반 참고값입니다.

## 설치

Codex 스킬 폴더에 클론합니다.

```bash
git clone https://github.com/Pandoll-AI/publish-skill.git ~/.codex/skills/publish-skill
```

이미 체크아웃한 폴더가 있다면 심볼릭 링크로 등록해도 됩니다.

```bash
ln -s /path/to/publish-skill ~/.codex/skills/publish-skill
```

Codex에서 이렇게 요청합니다.

```text
Use $publish-skill to polish this draft for publication with fact, logic, and style checks.
```

## 로컬 실행

네트워크 없이 결정적 스캐폴드를 실행할 수 있습니다. 이 실행은 claim audit과 evidence-gap marking에 가깝습니다.

```bash
python3 scripts/orchestrate_publish.py \
  --draft examples/korean_blog_draft.md \
  --output outputs/example_run \
  --language ko \
  --mode standard_publish \
  --fact-check mixed
```

출력 검증:

```bash
python3 scripts/validate_outputs.py outputs/example_run
```

테스트:

```bash
python3 tests/run_tests.py
```

실제 산출물 예시는 [examples/sample_output/korean_blog_draft](examples/sample_output/korean_blog_draft)를 확인하세요. 이 예시는 `revise_required` 상태를 포함하며, 로컬 scaffold가 검증 gap을 숨기지 않는 방식을 보여줍니다.

## 모드

- `audit_only`: 리라이트 없이 산출물과 gate만 생성.
- `light_edit`: 원래 구조를 유지하는 보수적 편집.
- `quick_polish`: 짧고 낮은 위험도의 문장 정리.
- `standard_publish`: 기본 출판 전 최종 패스.
- `publish_gate`: 엄격한 출판 가능 판정.
- `strong_rewrite`: 의미 보존을 전제로 더 강한 재구성 허용.
- `publish_ready`: 엄격 판정용 legacy alias.
- `high_risk_review`: 의료, 법률, 금융, 안전, 공공정책 주장에 대한 엄격 검토.
- `voice_rewrite`: 글쓴이의 목소리를 보존하는 리라이트.
- `explain_for_beginner`: 근거 없는 예시를 더하지 않는 쉬운 설명.
- `fact_check_only`: 주장과 근거 빈칸만 검토.
- `publication_style_only`: 문체 중심 산출물 생성.
- `logic_only`: 논리와 구조만 검토.

## 원칙

Publish Skill은 출처를 지어내지 않습니다. 근거가 없으면 `source needed`로 표시하거나, 문장의 강도를 낮추거나, 삭제합니다.

문체는 마지막입니다. 먼저 사실과 논리를 통과해야 합니다.

## 감사

Publish Skill은 공냥이 (@kimsh-1) 유저에게 deep inspiration을 받았고, 그 방향과 감각을 비슷하게 구현하려고 노력했습니다.

좋은 기준과 영감을 준 공냥이에게 감사드립니다.

## 변경 기록

변경 사항은 [CHANGELOG.md](CHANGELOG.md)를 확인하세요.

## 라이선스

MIT
