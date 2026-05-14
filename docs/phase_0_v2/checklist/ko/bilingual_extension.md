# Checklist (KO) — 이중 언어 확장 (EN / JP)

| | |
|---|---|
| FSD | [`../../fsd/bilingual_extension.md`](../../fsd/bilingual_extension.md) |
| Phase | Phase 3 — v2 제품 출시 |
| 언어 정보 | 영어 원본 [`../en/bilingual_extension.md`](../en/bilingual_extension.md) — 이 문서는 한국어 번역 |

---

## 기술 스택
- FSD §2 의 언어 인식 TTS / LLM / RAG / 컴플라이언스

---

## §1. 사전 준비 (활성화 전)
- [ ] 시장 검증: 셀러들이 EN 또는 JP 청중 요청 중인가?
- [ ] 우선순위 결정: EN 우선 vs JP 우선
- [ ] Re-bible 결정 (단일 현지화 마스코트 vs 언어별 별도)

## §2. 문화 적응
- [ ] 언어별 re-bible (직접 번역 X — 문화 특화 사장님 프레임 재작업 필요)
- [ ] 언어별 음성 ref
- [ ] 언어별 컴플라이언스 룰 (EN 미국 FTC, JP 일본 景品表示法)

## §3. 컴포넌트 업데이트
- [ ] TTS: 다국어 음성 프로필
- [ ] LLM Host: 언어별 페르소나 프롬프트
- [ ] LLM Moderator: 언어 인식 룰
- [ ] 스크립트 스키마: `language` 필드 이미 en/ja 지원 — 런타임 honor
- [ ] RAG: BGE-M3 이미 다국어; EN/JP 품질 검증

## §4. 파일럿
- [ ] 선택 언어로 방송 1개
- [ ] 원어민 검토
- [ ] 반복
