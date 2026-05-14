# Checklist (KO) — Analytics 대시보드

| | |
|---|---|
| FSD | [`../../fsd/analytics_dashboard.md`](../../fsd/analytics_dashboard.md) |
| Phase | Phase 3 (플랫폼 analytics API 의존) |
| 언어 정보 | 영어 원본 [`../en/analytics_dashboard.md`](../en/analytics_dashboard.md) — 이 문서는 한국어 번역 |

---

## 기술 스택
- 플랫폼 analytics API + ClickHouse 웨어하우스 + Grafana/React 시각화

---

## §1. 사전 준비
- [ ] 플랫폼 파트너십이 시청자 + 전환 데이터 접근 제공
- [ ] 전환 attribution 모델 결정 (in-stream 클릭 추적 + 체크아웃 픽셀)

## §2. 구현
- [ ] 플랫폼 analytics API 커넥터 (플랫폼별)
- [ ] analytics 이벤트용 ClickHouse 스키마 확장
- [ ] 대시보드 패널 구축 (FSD §3 메트릭 리스트)
- [ ] 테넌트별 접근 제어

## §3. 프라이버시
- [ ] 플랫폼별 PII 처리 검토
- [ ] 집계 기본값 (vs 시청자 수준 데이터)
- [ ] 보관 정책 `audit_log.md` 와 일치

## §4. 수용
- [ ] 셀러가 최소 다음 확인 가능: 방송당 시청자 peak/avg, 댓글 비율, 전환율
- [ ] 방송 종료 → 대시보드 데이터 지연 ≤ 24시간
