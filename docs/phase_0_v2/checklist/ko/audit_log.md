# Checklist (KO) — 감사 로그 (ClickHouse)

| | |
|---|---|
| 목적 | 방송 이벤트 로깅용 ClickHouse + ingester 구축 |
| FSD | [`../../fsd/audit_log.md`](../../fsd/audit_log.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/audit_log.md`](../en/audit_log.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **ClickHouse** (Apache 2.0) — 이벤트 저장소
- **clickhouse-driver** Python (MIT)
- **Redis** — 버퍼 + 프로듀서 파이프
- **인프라**: 전용 VM 또는 managed (ClickHouse Cloud) 의 ClickHouse

상세: [`../../fsd/audit_log.md`](../../fsd/audit_log.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/audit_log.md`](../../fsd/audit_log.md) 읽기
- [ ] ClickHouse 인스턴스 프로비저닝
- [ ] env 에 연결 정보

## §2. 스키마

- [ ] FSD §3.1 의 `broadcast_events` 테이블 생성
- [ ] §3.2 의 `decision_audit` materialized view 생성
- [ ] partitioning + ORDER BY 확인

## §3. Ingester 서비스

- [ ] Redis 토픽 `broadcast.audit.<id>` 구독
- [ ] 10초 버퍼링, bulk insert
- [ ] ClickHouse backpressure 처리: bounded Redis 버퍼, full 시 alert

## §4. Replay 테스트

- [ ] 테스트 방송 end-to-end 실행
- [ ] 해당 방송 이벤트 ClickHouse 에서 replay 쿼리
- [ ] 예상 이벤트 수와 비교 완전성 확인

## §5. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 | ⬜ |
| §2 스키마 | ⬜ |
| §3 Ingester | ⬜ |
| §4 Replay 테스트 | ⬜ |

## §6. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| ClickHouse insert 에러 | 스키마 버전 관리; 비호환 변경 시 새 테이블로 rotate |
| 버퍼 가득 참 | ingester 스케일 업; ClickHouse insert 용량 증가 |
| Replay 이벤트 누락 | 에이전트 간 프로듀서 계측 확인 |
