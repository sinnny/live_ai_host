# Checklist — Object storage

| | |
|---|---|
| Purpose | Set up MinIO (MVP) or Cloudflare R2 (scale) for tenant-isolated asset storage |
| FSD | [`../../fsd/storage.md`](../../fsd/storage.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/storage.md`](../ko/storage.md) |

---

## Tech stack (at a glance)

- **MinIO** (AGPL) — self-hosted MVP
- **Cloudflare R2** — managed, free egress (optional scale path)
- IAM via MinIO or Cloudflare policy
- **Infra**: dedicated VM or managed

Full table: [`../../fsd/storage.md`](../../fsd/storage.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/storage.md`](../../fsd/storage.md) read
- [ ] [`multi_tenancy.md`](multi_tenancy.md) read (IAM policy)

## §2. Provision

- [ ] MinIO container running OR R2 bucket created
- [ ] S3 credentials in env

## §3. Layout setup

- [ ] Confirm bucket structure per FSD §3
- [ ] Lifecycle rules: 30-day cold tier, 1-year expiry

## §4. IAM policy

- [ ] Per-tenant policy applied
- [ ] Cross-tenant read test passes

## §5. Integration test

- [ ] `make_mascot` writes atlas to `s3://.../<tenant_id>/mascots/...`
- [ ] Operator dashboard reads via signed URL

## §6. Status board

| Step | Status |
|---|---|
| §1 Prerequisites | ⬜ |
| §2 Provision | ⬜ |
| §3 Layout | ⬜ |
| §4 IAM | ⬜ |
| §5 Integration | ⬜ |

## §7. Troubleshooting

| Issue | Response |
|---|---|
| Signed URL fails | check expiry + clock sync |
| Write throughput low | tune MinIO concurrency settings |
| Cross-tenant access leak | review IAM policy; test with explicit deny |
