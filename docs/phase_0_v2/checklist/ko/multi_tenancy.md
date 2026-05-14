# Checklist (KO) — Multi-tenancy

| | |
|---|---|
| 목적 | DB, vector DB, 스토리지, auth 레이어에서 테넌트 격리 적용 |
| FSD | [`../../fsd/multi_tenancy.md`](../../fsd/multi_tenancy.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/multi_tenancy.md`](../en/multi_tenancy.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Postgres RLS** — 행 수준 격리
- **Qdrant** 방송별 컬렉션 (이미 적용)
- **S3 IAM** — 버킷 prefix 격리
- **OAuth + JWT** — role claim 포함 auth
- **인프라**: `data_model.md` 및 `storage.md` 와 동일

상세: [`../../fsd/multi_tenancy.md`](../../fsd/multi_tenancy.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/multi_tenancy.md`](../../fsd/multi_tenancy.md) 읽기
- [ ] [`data_model.md`](data_model.md) DB 준비 완료
- [ ] [`storage.md`](storage.md) S3 준비 완료

## §2. Postgres RLS

- [ ] [`data_model.md`](data_model.md) 체크리스트 §3 에 따라 RLS 활성화
- [ ] 교차 테넌트 읽기 테스트 통과 (테넌트 A 가 B 읽기 불가)

## §3. Qdrant 격리

- [ ] 방송별 컬렉션 명명 확인 (`broadcast_<id>_products`)
- [ ] 교차 방송 쿼리 테스트: 잘못된 컬렉션 쿼리 시 empty 반환

## §4. S3 IAM

- [ ] 테넌트별 prefix IAM 정책 적용
- [ ] 교차 테넌트 접근 테스트: 테넌트 A 가 `s3://.../tenant_b/...` 읽기 불가

## §5. Auth + RBAC

- [ ] JWT 에 `tenant_id` + `role` claim 포함
- [ ] FSD §3.4 의 role-permission 매트릭스 테스트

## §6. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 | ⬜ |
| §2 Postgres RLS | ⬜ |
| §3 Qdrant 격리 | ⬜ |
| §4 S3 IAM | ⬜ |
| §5 Auth + RBAC | ⬜ |

## §7. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| RLS 우회 성공 | 정책 활성화 + 연결이 설정 적용 확인 |
| 교차 테넌트 Qdrant 누출 | 컬렉션 명명 일관성 확인 |
| JWT claim 누락 | IDP 커스텀 claim 구성 확인 |
