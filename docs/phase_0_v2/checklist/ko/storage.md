# Checklist (KO) — Object 스토리지

| | |
|---|---|
| 목적 | 테넌트 격리된 자산 스토리지를 위한 MinIO (MVP) 또는 Cloudflare R2 (확장) 구성 |
| FSD | [`../../fsd/storage.md`](../../fsd/storage.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/storage.md`](../en/storage.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **MinIO** (AGPL) — self-host MVP
- **Cloudflare R2** — managed, free egress (선택 확장 경로)
- MinIO 또는 Cloudflare 정책 통한 IAM
- **인프라**: 전용 VM 또는 managed

상세: [`../../fsd/storage.md`](../../fsd/storage.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/storage.md`](../../fsd/storage.md) 읽기
- [ ] [`multi_tenancy.md`](multi_tenancy.md) 읽기 (IAM 정책)

## §2. 프로비저닝

- [ ] MinIO 컨테이너 실행 또는 R2 버킷 생성
- [ ] env 에 S3 자격증명

## §3. 레이아웃 설정

- [ ] FSD §3 의 버킷 구조 확인
- [ ] Lifecycle 규칙: 30일 cold tier, 1년 만료

## §4. IAM 정책

- [ ] 테넌트별 정책 적용
- [ ] 교차 테넌트 읽기 테스트 통과

## §5. 통합 테스트

- [ ] `make_mascot` 가 atlas 를 `s3://.../<tenant_id>/mascots/...` 에 작성
- [ ] Operator 대시보드가 signed URL 로 읽음

## §6. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 | ⬜ |
| §2 프로비저닝 | ⬜ |
| §3 레이아웃 | ⬜ |
| §4 IAM | ⬜ |
| §5 통합 | ⬜ |

## §7. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| Signed URL 실패 | 만료 + 시계 동기화 확인 |
| 쓰기 처리량 낮음 | MinIO 동시성 설정 튜닝 |
| 교차 테넌트 접근 누출 | IAM 정책 검토; 명시적 deny 로 테스트 |
