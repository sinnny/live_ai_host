# Checklist (KO) — Data model (Postgres)

| | |
|---|---|
| 목적 | Alembic 마이그레이션 포함 Postgres 스키마 구현 |
| FSD | [`../../fsd/data_model.md`](../../fsd/data_model.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/data_model.md`](../en/data_model.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Postgres 16+** (PostgreSQL)
- **SQLAlchemy 2.x** (MIT) — ORM
- **Alembic** (MIT) — 마이그레이션
- **pgbouncer** (BSD-3) — 연결 풀링
- **인프라**: managed Postgres (AWS RDS / Render / Supabase) 또는 self-host

상세: [`../../fsd/data_model.md`](../../fsd/data_model.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/data_model.md`](../../fsd/data_model.md) 읽기
- [ ] [`multi_tenancy.md`](multi_tenancy.md) 읽기 (RLS 전략)
- [ ] Postgres 16+ 인스턴스 프로비저닝
- [ ] env 에 DB 연결 문자열

## §2. 스키마 구현

- [ ] FSD §3 의 SQLAlchemy 모델 정의
- [ ] Alembic baseline 마이그레이션 생성: `alembic revision --autogenerate -m "baseline"`
- [ ] SQL 검토 — FSD §4 의 인덱스 확인
- [ ] 적용: `alembic upgrade head`

## §3. RLS 설정

- [ ] 모든 multi-tenant 테이블에서 RLS 활성화
- [ ] `app.tenant_id` 설정 사용한 RLS 정책 추가 ([`multi_tenancy.md`](multi_tenancy.md) §3.1)
- [ ] 테스트: tenant A 로 연결, tenant B 행 읽기 시도 → 차단됨

## §4. 시드 데이터

- [ ] 시스템 마스코트 (다람찌) 삽입
- [ ] 개발용 테스트 테넌트 삽입
- [ ] 테스트 제품 삽입

## §5. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 | ⬜ |
| §2 스키마 | ⬜ |
| §3 RLS | ⬜ |
| §4 시드 | ⬜ |

## §6. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| 마이그레이션 충돌 | 수동으로 해결; revision 자동 머지 안함 |
| RLS 미적용 | 모든 연결에 `current_setting('app.tenant_id')` 설정 확인 |
| 방송 리스트 쿼리 느림 | `(tenant_id, scheduled_start)` 인덱스 확인 |
