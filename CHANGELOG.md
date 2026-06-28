# Changelog

## 0.3.0

- 공개 포지셔닝을 `v0.3.0 scaffold`로 낮췄습니다.
- README/manifest/SKILL에서 live fact-checking처럼 보일 수 있는 표현을 완화했습니다.
- manifest, SKILL, validator의 required output contract와 mode 목록을 맞췄습니다.
- `final_verdict.json`의 `scores`를 `heuristic_scores`와 `score_basis`로 바꿔 규칙 기반 참고값임을 명시했습니다.
- `semantic_diff.json`에 `method: surface_claim_diff`와 한계 설명을 추가했습니다.
- 정적 validation/test 배지를 제거하고 로컬 검증 명령 중심으로 문서화했습니다.
- package audit에 version, mode, output, README badge contract 검사를 추가했습니다.

## 2026-06-28

- 공개 README를 한국어 기본 문서로 전환했습니다.
- English 버튼을 추가해 `README.en.md`로 이동할 수 있게 했습니다.
- GitHub 배지를 중앙 정렬하고 저장소 상태 배지를 확장했습니다.
- 히어로 이미지를 한글 인포그래픽 SVG로 교체했습니다.
- 변경 기록 문서를 추가했습니다.

## 0.2.0

- Publish Skill 공개 릴리스.
- 주장 점검, 논리 게이트, 문체 게이트, 의미 차이 검토를 포함한 출판 전 최종 패스 구조를 정리했습니다.
- 의료, 법률, 금융, 안전, 공공정책 등 고위험 주장에 대한 엄격 모드를 추가했습니다.
